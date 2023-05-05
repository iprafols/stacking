#!/usr/bin/env bash

for file in bin/*py stacking/*py stacking/*/*py
do
  echo "yapf --style google $file -i"
  yapf --style google $file -i
done
