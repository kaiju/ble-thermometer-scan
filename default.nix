{ pkgs ? import <nixpkgs> { } }:
pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./.;
  overrides = [
    pkgs.poetry2nix.defaultPoetryOverrides
  ];
}

