include Makefile.mk
USERNAME=mvanholsteijn
NAME=marathon-release

on-tag:
	sed -e "s/version=.*/version='$(VERSION)',/" -i "" setup.py
