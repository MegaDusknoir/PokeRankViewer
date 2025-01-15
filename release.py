import subprocess
import zipfile
import os
import sys

if __name__ == '__main__':
    workDir = os.path.dirname(sys.argv[0])
    result = subprocess.run(f'pyinstaller "{workDir}/pokeHomeGui.py" -F -w -y -i "{workDir}/home.ico" -n "PokeHOME RankViewer" --distpath "{workDir}/."', stdout=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print(f'Pyinstaller fail at {result.returncode}')
        exit()

    if os.path.isdir(f'{workDir}/release') == False:
        os.makedirs(f'{workDir}/release')
    with zipfile.ZipFile(f"{workDir}/release/PokeHOME RankViewer.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isdir(f'{workDir}/raw'):
            for file in os.listdir(f'{workDir}/raw'):
                zf.write(f'{workDir}/raw/{file}', f'raw/{file}')
        zf.write(f"{workDir}/PokeHOME RankViewer.exe", "PokeHOME RankViewer.exe")
    print(f'Packed')