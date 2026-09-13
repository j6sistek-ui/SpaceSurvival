// Test-only Windows oplock owner. No installer, runtime hooks, or production paths.
// Loaded by TestSaveLifecycle.ps1; all unmanaged buffers outlive their pending I/O.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using Microsoft.Win32.SafeHandles;

namespace SpaceSurvival.SaveFaults
{
    public sealed class ReplacementGate : IDisposable
    {
        [StructLayout(LayoutKind.Sequential)]
        private struct Request { public ushort Version, Length; public uint Level, Flags; }
        [StructLayout(LayoutKind.Sequential)]
        public struct BreakInfo
        {
            public ushort Version, Length;
            public uint OriginalLevel, NewLevel, Flags, AccessMode;
            public ushort ShareMode;
        }
        [StructLayout(LayoutKind.Sequential)]
        private struct Overlapped
        {
            public IntPtr Internal, InternalHigh;
            public uint Offset, OffsetHigh;
            public IntPtr Event;
        }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security,
                                                         uint disposition, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool DeviceIoControl(SafeFileHandle file, uint code, IntPtr input, uint inputSize,
                                                   IntPtr output, uint outputSize, out uint bytes, IntPtr overlapped);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetOverlappedResult(SafeFileHandle file, IntPtr overlapped, out uint bytes, bool wait);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CancelIoEx(SafeFileHandle file, IntPtr overlapped);

        private SafeFileHandle file;
        private EventWaitHandle completed;
        private IntPtr input, output, overlapped;
        private bool pending, breakReceived;
        private Process writer;
        public BreakInfo Break { get; private set; }

        public ReplacementGate(string repository, string root, string token)
        {
            Guid parsed;
            if (!Guid.TryParseExact(token, "N", out parsed)) throw new ArgumentException("Invalid fixture GUID.");
            repository = Path.GetFullPath(repository);
            root = Path.GetFullPath(root);
            if (!String.Equals(root, Path.Combine(repository, "Artifacts", "SaveLifecycle", token), StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("Oplock root is not the exact repository GUID fixture.");
            string target = Path.Combine(root, "User", "Saved", "SaveGames", "SS_Suspend_v1.sav");
            for (string path = target; path != null; path = Path.GetDirectoryName(path))
                if ((File.Exists(path) || Directory.Exists(path)) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
                    throw new IOException("Oplock path is redirected: " + path);
            string marker = Path.Combine(root, ".ss-save-lifecycle");
            if ((File.GetAttributes(marker) & FileAttributes.ReparsePoint) != 0 || File.ReadAllText(marker).Trim() != token)
                throw new IOException("Oplock fixture marker is invalid.");
            try
            {
                // Read sharing permits GI checkpoint reads; deny write/delete sharing. A conflicting
                // replacement must break this Read-Handle oplock and wait for acknowledgement.
                file = CreateFileW(target, 0x80000000, 1, IntPtr.Zero, 3, 0x40000000, IntPtr.Zero);
                if (file.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error(), "Open isolated oplock target");
                completed = new EventWaitHandle(false, EventResetMode.ManualReset);
                Request request = new Request { Version = 1, Length = (ushort)Marshal.SizeOf(typeof(Request)), Level = 3, Flags = 1 };
                input = Marshal.AllocHGlobal(request.Length);
                Marshal.StructureToPtr(request, input, false);
                int outputLength = Marshal.SizeOf(typeof(BreakInfo));
                output = Marshal.AllocHGlobal(outputLength);
                Marshal.Copy(new byte[outputLength], 0, output, outputLength);
                Overlapped operation = new Overlapped { Event = completed.SafeWaitHandle.DangerousGetHandle() };
                overlapped = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(Overlapped)));
                Marshal.StructureToPtr(operation, overlapped, false);
                uint bytes;
                bool immediate = DeviceIoControl(file, 0x00090240, input, request.Length, output,
                                                  (uint)outputLength, out bytes, overlapped);
                int error = Marshal.GetLastWin32Error();
                if (immediate || error != 997)
                    throw new Win32Exception(error, "A pending Read-Handle oplock was not granted");
                pending = true;
            }
            catch { Dispose(); throw; }
        }

        public void BindWriter(Process ownedWriter)
        {
            if (writer != null || ownedWriter == null) throw new InvalidOperationException("Writer binding is immutable.");
            writer = ownedWriter;
        }

        public bool WaitForBreak(int milliseconds)
        {
            if (milliseconds < 0 || milliseconds > 1000) throw new ArgumentOutOfRangeException("milliseconds");
            if (breakReceived) return true;
            if (!completed.WaitOne(milliseconds)) return false;
            uint bytes;
            if (!GetOverlappedResult(file, overlapped, out bytes, false))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Read oplock break result");
            pending = false;
            Break = (BreakInfo)Marshal.PtrToStructure(output, typeof(BreakInfo));
            if (Break.Version != 1 || bytes < 22 || (Break.OriginalLevel & 2) == 0 || (Break.Flags & 1) == 0)
                throw new IOException("The observed oplock break does not require acknowledgement; no interruption proof.");
            breakReceived = true;
            return true;
        }

        public void Dispose()
        {
            if (writer != null && !writer.HasExited)
                throw new InvalidOperationException("Refusing to release the oplock while its owned writer is alive.");
            if (file != null && !file.IsClosed && !file.IsInvalid && pending)
            {
                CancelIoEx(file, overlapped);
                if (!completed.WaitOne(5000))
                    throw new IOException("Oplock cancellation did not complete; buffers remain allocated for I/O safety.");
                pending = false;
            }
            if (file != null) { file.Dispose(); file = null; }
            if (input != IntPtr.Zero) { Marshal.FreeHGlobal(input); input = IntPtr.Zero; }
            if (output != IntPtr.Zero) { Marshal.FreeHGlobal(output); output = IntPtr.Zero; }
            if (overlapped != IntPtr.Zero) { Marshal.FreeHGlobal(overlapped); overlapped = IntPtr.Zero; }
            if (completed != null) { completed.Dispose(); completed = null; }
        }
    }
}
