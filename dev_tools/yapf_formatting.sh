#!/usr/bin/env bash

for file in stacking/*py stacking/*/*py
do
  echo "yapf --style google $file -i"
  yapf --style google $file -i
done
