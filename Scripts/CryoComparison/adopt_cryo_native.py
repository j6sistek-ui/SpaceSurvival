"""New-only local native adoption; preserves owner content and unrelated text bytes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, shutil

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / 'outputs/Cryo_Comparison'
OWNER = Path('C:/Users/j6sis/SpaceSurvival')
REL = Path('Content/SpaceSurvival/CryoComparison')
SOURCE = WORK / 'CryoStage' / REL
TARGET = OWNER / REL

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(apply=False):
    assert SOURCE.is_dir() and not TARGET.exists(), 'Only a new namespace can be adopted'
    assert not SOURCE.is_symlink() and not TARGET.parent.is_symlink()
    files = sorted(p for p in SOURCE.rglob('*') if p.is_file())
    assert all(p.suffix in ('.uasset', '.umap', '.ubulk', '.uexp') and not p.is_symlink() for p in files)
    donor = json.loads((WORK/'niagara-source-copy.json').read_text())
    for item in donor:
        assert sha(OWNER/'Content'/item['relative_path']) == item['sha256'], 'Donor changed; stop'
    baseline = json.loads((WORK/'CryoFinalAuthor.json').read_text())
    assert all(sha(Path(p)) == row['sha256'] for p,row in baseline['source_files'].items())
    ini = OWNER/'Config/DefaultGame.ini'
    ignore = OWNER/'.gitignore'
    config = ini.read_bytes()
    ignored = ignore.read_bytes()
    line = b'+DirectoriesToNeverCook=(Path="/Game/SpaceSurvival/CryoComparison")'
    section = b'[/Script/UnrealEd.ProjectPackagingSettings]'
    assert config.count(section) == 1
    newline = b'\r\n' if b'\r\n' in config else b'\n'
    assert line not in config
    updated = config.replace(section, section+newline+line, 1)
    ignored_line = b'/Content/SpaceSurvival/CryoComparison/'
    assert ignored_line not in ignored
    updated_ignore = ignored.rstrip(b'\r\n')+newline+newline+b'# Local four-chamber comparison assets.'+newline+ignored_line+newline
    manifest = [{'relative_path':p.relative_to(SOURCE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
    receipt = {'utc':datetime.now(timezone.utc).isoformat(), 'apply':apply, 'status':'DRY_RUN_VALIDATED',
        'destination':str(TARGET), 'files':manifest, 'file_count':len(files),
        'bytes':sum(r['bytes'] for r in manifest), 'donor_files_unchanged':len(donor),
        'original_and_import_hashes_unchanged':len(baseline['source_files']),
        'owner_loaded_in_editor':False,
        'config_changes':['Exact CryoComparison NeverCook entry','Exact local native namespace gitignore entry'],
        'owner_before':{str(ini):sha(ini),str(ignore):sha(ignore)}}
    if apply:
        backup = WORK/'owner-adoption-before'
        backup.mkdir(exist_ok=False)
        (backup/'DefaultGame.ini').write_bytes(config)
        (backup/'gitignore').write_bytes(ignored)
        # Exclusive destination and post-copy digest verification precede text edits.
        TARGET.mkdir(parents=False, exist_ok=False)
        for source,row in zip(files,manifest):
            destination = TARGET/row['relative_path']
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
            assert sha(destination) == row['sha256']
        assert ini.read_bytes() == config and ignore.read_bytes() == ignored, 'Owner text changed during copy'
        ini.write_bytes(updated)
        ignore.write_bytes(updated_ignore)
        assert ini.read_bytes().replace(section+newline+line,section,1) == config
        assert ignore.read_bytes() == updated_ignore
        receipt['status']='ADOPTED_NEW_NAMESPACE_HASH_VERIFIED'
        receipt['owner_after']={str(ini):sha(ini),str(ignore):sha(ignore)}
        receipt['backup_directory']=str(backup)
    dest=OUT/('native-adoption.json' if apply else 'native-adoption-dry-run.json')
    dest.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ('status','file_count','bytes','destination')}))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    main(parser.parse_args().apply)
