"""Copy a versioned fit package to the Mac and verify it before moving its alias."""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
HOST='sunils-mac-mini.lan'
REMOTE='/Users/sunil/Downloads/Tinfox'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result',type=Path,required=True)
    parser.add_argument('--alias',choices=['Current-Motor-Fit','Current-Motor-Complex'],required=True)
    args=parser.parse_args();release=json.loads(args.result.read_text());archive=Path(release['archive']).resolve();label=archive.stem
    assert archive.is_relative_to(ROOT/'output/print-handoff') and re.fullmatch(r'Tinfox-[A-Za-z0-9-]+',label)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==release['archive_sha256']
    if args.alias=='Current-Motor-Complex':
        manifest=json.loads((Path(release['directory'])/'manifest.json').read_text())
        native=(ROOT/'fusion_native').resolve()
        authority_path=(native/manifest.get('source_manifest_relative','manifests/motor-complex-native-exports.json')).resolve()
        assert authority_path.is_relative_to(native/'manifests') and authority_path.is_file()
        authority=json.loads(authority_path.read_text())
        assert authority.get('assembly_release_ready') is True and authority.get('native_source_of_truth') is True
        assert manifest['source_manifest_sha256']==hashlib.sha256(authority_path.read_bytes()).hexdigest()
        assert manifest['source_kind']=='fusion-native'
    remote_file=REMOTE+'/'+archive.name
    exists=subprocess.run(['ssh','-o','BatchMode=yes',HOST,'test -e '+shlex.quote(remote_file)],capture_output=True)
    assert exists.returncode in [0,1],exists.stderr.decode()
    if exists.returncode==0:
        digest=subprocess.check_output(['ssh','-o','BatchMode=yes',HOST,'shasum -a 256 '+shlex.quote(remote_file)],text=True).split()[0]
        assert digest==release['archive_sha256'],'Refusing to overwrite a different existing remote archive.'
    else:subprocess.run(['scp','-q','-o','BatchMode=yes',str(archive),HOST+':'+REMOTE+'/'],check=True)
    script='''set -eu
cd /Users/sunil/Downloads/Tinfox
tinfox_release="$1"
tinfox_expected="$2"
tinfox_alias="$3"
[ "$(shasum -a 256 "$tinfox_release.zip" | awk '{print $1}')" = "$tinfox_expected" ]
unzip -t "$tinfox_release.zip" > /dev/null
unzip -q -n "$tinfox_release.zip"
(cd "$tinfox_release" && shasum -a 256 -c SHA256SUMS)
if [ -L "$tinfox_alias" ]; then
 case "$(readlink "$tinfox_alias")" in Tinfox-Motor-Fit-*|Tinfox-Motor-Interface-Fit-*|Tinfox-Native-Motor-Fit-*|Tinfox-Native-Motor-Complex-*|Tinfox-Motor-Complex-*) ;; *) exit 31;; esac
elif [ -e "$tinfox_alias" ]; then exit 32
fi
ln -sfn "$tinfox_release" "$tinfox_alias"
[ "$(readlink "$tinfox_alias")" = "$tinfox_release" ]
'''
    command='sh -s -- '+' '.join(shlex.quote(value) for value in [label,release['archive_sha256'],args.alias])
    result=subprocess.run(['ssh','-o','BatchMode=yes',HOST,command],input=script,text=True,capture_output=True,check=True)
    report={'package':label,'archive_sha256':release['archive_sha256'],'mac_alias':REMOTE+'/'+args.alias,
        'files_verified':result.stdout.count(': OK'),'alias_verified':True,'printing_started':False}
    archive.with_name(label+'-mac-delivery.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()
