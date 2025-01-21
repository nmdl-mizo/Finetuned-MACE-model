#!/bin/bash
docker run --rm --entrypoint make -v $PWD:/work -w /work ghcr.io/kiyou/latex:latest $1
