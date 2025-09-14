#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This script can automatically generate blockstate and block model files for the Round Trees resourcepack."""

import argparse
import json
import os
import zipfile
import shutil
import time
from distutils.dir_util import copy_tree

# Utility functions
def printGreen(out): print("\033[92m{}\033[00m".format(out))
def printCyan(out): print("\033[96m{}\033[00m" .format(out))
def printOverride(out): print(" -> {}".format(out))

def autoGen(jsonData, args):
    print("Generating assets...")
    if (os.path.exists("./assets")): shutil.rmtree("./assets")
    copy_tree("./base/assets/", "./assets/")
    filecount = 0
    unpackMods()
    scanModsForLogs()

    for root, dirs, files in os.walk("./input/assets"):
        for infile in files:
            if (len(root.split("/")) > 3) and root.endswith("models/block"):
                namespace = root.split("/")[3]
                block_id = infile.replace(".json", "")
                print(namespace+":"+block_id)
                textures = readTextures(root, infile, namespace, block_id)

                generateBlockstateAndModel(namespace, block_id, textures["end"], textures["side"])
                filecount += 1
    # End of autoGen
    print()
    cleanupMods()
    printCyan("Processed {} log blocks".format(filecount))

def readTextures(root, infile, namespace, block_id) -> dict[str, str]:
    with open(os.path.join(root, infile), "r") as rf:
        textures = json.load(rf)["textures"]
        texture_end = None
        texture_side = None
        for key in ["end", "up"]:
            if key in textures:
                texture_end = textures[key]
                break
        for key in ["side", "north"]:
            if key in textures:
                texture_side = textures[key]
                break
        if texture_end == None:
            printOverride("Could not determine top texture in base model, using fallback")
            texture_end = f"{namespace}:{block_id}_top"
        if texture_side == None:
            printOverride("Could not determine side texture in base model, using fallback")
            texture_side = f"{namespace}:{block_id}"
        return {"end": texture_end, "side": texture_side}

def unpackMods():
    for root, dirs, files in os.walk("./input/mods"):
        for infile in files:
            if infile.endswith(".jar"):
                print("Unpacking mod: "+infile)
                zf = zipfile.ZipFile(os.path.join(root, infile), 'r')
                zf.extractall(os.path.join(root, infile.replace(".jar", "_temp")))
                zf.close()

def cleanupMods():
    if (os.path.exists("./input/mods")): shutil.rmtree("./input/mods")
    os.makedirs("./input/mods")

def scanModsForLogs():
    for root, dirs, files in os.walk("./input/mods"):
        for infile in files:
            if len(root.split("assets")) > 1:
                assetpath = root.split("assets")[1][1:]
                modid = assetpath.split("models/block")[0].replace("/", "")
                if "models/block" in root and infile.endswith("_log.json"):
                    print(f"Found log model {assetpath}/{infile} in mod {modid}")
                    inputfolder = os.path.join("./input/assets/", assetpath)
                    os.makedirs(inputfolder, exist_ok=True)
                    shutil.copyfile(os.path.join(root, infile), os.path.join(inputfolder, infile))

def generateBlockstateAndModel(mod_namespace, block_name, texture_end, texture_side, texture_inner = None):

    # Create structure for blockstate file
    block_state_file = f"assets/{mod_namespace}/blockstates/{block_name}.json"
    block_state_data = {
        "variants": {
            "axis=y":  { "model": f"{mod_namespace}:block/{block_name}" },
            "axis=z":   { "model": f"{mod_namespace}:block/{block_name}", "x": 90, "y": 180 },
            "axis=x":   { "model": f"{mod_namespace}:block/{block_name}", "x": 90, "y": 90, "z": 90 }
        }
    }

    # Create blockstates folder if it doesn't exist already
    if not os.path.exists("assets/{}/blockstates/".format(mod_namespace)):
        os.makedirs("assets/{}/blockstates/".format(mod_namespace))

    # Write blockstate file
    with open(block_state_file, "w") as f:
        json.dump(block_state_data, f, indent=4)


    # Create models folder if it doesn't exist already
    if not os.path.exists("assets/{}/models/block/".format(mod_namespace)):
        os.makedirs("assets/{}/models/block/".format(mod_namespace))

    # Create structure for block model file
    block_model_file = f"assets/{mod_namespace}/models/block/{block_name}.json"
    if "hollow_" in block_name:
        block_name = block_name.replace("hollow_", "")
        block_model_data = {
            "parent": "block/hollow_log",
            "textures": {
                "top": texture_end,
                "side": texture_side,
                "inner": texture_inner
            }
        }
    else:
        block_model_data = {
            "parent": "block/log",
            "textures": {
                "top": texture_end,
                "side": texture_side
            }
        }
    with open(block_model_file, "w") as f:
        json.dump(block_model_data, f, indent=4)

def generateItemModel(mod_namespace, block_name):
    # Create models folder if it doesn't exist already
    if not os.path.exists("assets/{}/models/item/".format(mod_namespace)):
        os.makedirs("assets/{}/models/item/".format(mod_namespace))

    item_model_file = f"assets/{mod_namespace}/models/item/{block_name}.json"
    item_model_data = {
        "parent": f"{mod_namespace}:block/{block_name}1"
    }
    with open(item_model_file, "w") as f:
        json.dump(item_model_data, f, indent=4)

def writeMetadata(args):
    edition = args.edition
    if isinstance(edition, list): edition = " ".join(args.edition)
    with open("./input/pack.mcmeta") as infile, open("pack.mcmeta", "w") as outfile:
        for line in infile:
            line = line.replace("${version}", args.version).replace("${edition}", edition).replace("${year}", str(time.localtime().tm_year))
            outfile.write(line)

# See https://stackoverflow.com/a/1855118
def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file),
                                       os.path.join(path, '..')))

def makeZip(filename):
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir('assets/', zipf)
        zipf.write('pack.mcmeta')
        zipf.write('pack.png')
        zipf.write('LICENSE')
        zipf.write('README.md')



# This is the main entry point, executed when the script is run
if __name__ == '__main__':
    start_time = time.perf_counter()
    parser = argparse.ArgumentParser(
                    description='This script can automatically generate files for the Round Trees resourcepack.',
                    epilog='Feel free to ask for help at http://discord.midnightdust.eu/')

    parser.add_argument('version', type=str)
    parser.add_argument('edition', nargs="*", type=str, default="§cCustom Edition", help="Define your edition name")
    args = parser.parse_args()

    print(args)
    print()

    # Loads overrides from the json file
    f = open('./input/overrides.json')
    data = json.load(f)
    f.close()

    autoGen(data, args);
    writeMetadata(args)
    print()
    print("Zipping it up...")
    makeZip(f"Round-Trees-{args.version}.zip");
    print("Done!")
    print("--- Finished in %s seconds ---" % (round((time.perf_counter() - start_time)*1000)/1000))
