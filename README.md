Master Go AI README

Welcome to the Master Go AI repository! This repository is home to an advanced Go AI engine designed to provide both newcomers and seasoned players with a robust tool for enhancing their Go skills.

Overview
After AlphaGo's historic victory over a world champion, deep learning has become synonymous with computer Go, sparking considerable interest. Our project, dlgo, implements a minimal Go engine that includes essential algorithms, a GTP interface, and SGF format parsing, allowing users to bypass the tedious aspects and focus on deep learning to experience the enchantment of computer Go.

Getting Started
Before starting, you will need to install the following Python dependencies (note that this program uses Python3):

PyTorch (version 1.x, download the corresponding CUDA/cuDNN version if using a GPU)
NumPy
Tkinter

Use the following command to install the required libraries, or download an executable version if preferred:

pip3 install -r requirements.txt

After installing the dependencies, download the source code and pre-trained weights available in the Releases section (as a .pt file, no decompression needed). Assuming the weight file is named nn_2x64.pt, use the following command to launch the graphical interface:

python3 dlgo.py --weights nn_2x64.pt --gui

Documentation Directory

Quick Start and Operational Tutorial: A simple guide on how to get started and operate the AI.

Algorithm Implementation and Principles (Under Construction)

GTP Interface Principles

SGF Format Explanation

Functions within board.py

List of Python Go Engines (contributions welcome)
