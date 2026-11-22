#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build either enclosure from a fresh Git checkout; never modify the PCB repo."""
from pathlib import Path
import argparse,subprocess,sys,os,json
from restore_references import restore
ROOT=Path(__file__).resolve().parents[1]
def main():
    projects=json.loads((ROOT/'projects.json').read_text())
    ap=argparse.ArgumentParser();ap.add_argument('project',choices=['simple','deluxe','keycaps'],nargs='?',default='simple');ap.add_argument('--allow-missing-external',action='store_true',help='Geometry validation only when vendor/PCB sources are unavailable; never ignore changed hashes');ap.add_argument('--check-only',action='store_true');ap.add_argument('--package',action='store_true',help='Requires complete external source verification');args=ap.parse_args()
    name=projects['aliases'].get(args.project,args.project)
    if name=="simple":restore()
    root=ROOT/projects['projects'][name]['path'];simple=name=='simple'
    python=Path(sys.executable)
    check=subprocess.run([str(python),'-c','import cadquery,numpy,PIL,numba,scipy,ezdxf'],capture_output=True)
    if check.returncode:raise SystemExit('Install simple/source/requirements.txt into .venv first; see docs/build.md')
    (root/'.work').mkdir(exist_ok=True);log_path=root/'.work/build.log'
    def run(command,log):
        print('Run:',Path(command[-1]).name if len(command)==2 else ' '.join(map(str,command[1:])),flush=True)
        result=subprocess.run(list(map(str,command)),cwd=root,stdout=log,stderr=subprocess.STDOUT)
        log.flush()
        if result.returncode:
            print('\n'.join(log_path.read_text(errors='replace').splitlines()[-25:]));raise SystemExit(result.returncode)
    with log_path.open('w') as log:
        if not args.check_only:run([python,root/'source'/('generate_simple.py' if simple else 'generate_enclosure.py')],log)
        command=[python,root/'source/verify_outputs.py']
        if args.allow_missing_external:command.append('--allow-missing-external')
        run(command,log)
        if simple:run([python,root/'source/review_deck_change.py'],log)
        if not args.check_only:
            run([python,root/'source'/('render_simple.py' if simple else 'render_enclosure.py')],log)
            run([python,root/'source/create_drawings.py'],log)
            if not simple:run(['/usr/bin/python3',ROOT/'tools/render_svg.py',root/'preview/dimensions.svg'],log)
            run([python,root/'source/make_gallery.py'],log)
        if args.package:run([python,root/'source'/('package_simple.py' if simple else 'package_enclosure.py')],log)
    print('Complete:',root,'\nLog:',log_path)
if __name__=='__main__':main()
