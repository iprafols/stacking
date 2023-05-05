#!/usr/bin/env bash

for file in bin/*py stacking/*py stacking/*/*py
do
  yapf --style google $file -i
done
