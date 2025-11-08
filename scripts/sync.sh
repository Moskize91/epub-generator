#!/bin/bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

rm -rf ../../oomol-lab/pdf-craft/epub_generator
cp -r ./epub_generator ../../oomol-lab/pdf-craft/epub_generator