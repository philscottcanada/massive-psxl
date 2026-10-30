"""Rebuilds every PDF: python tools/docs/build_all.py   (needs: pip install reportlab)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_manual, build_video_scripts
build_manual.main()
build_video_scripts.main()
