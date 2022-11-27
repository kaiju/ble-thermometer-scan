{ pkgs ? import <nixpkgs> { } }:
pkgs.poetry2nix.mkPoetryApplication {
  name = "ble-thermometer-scan";
  version = "0.2";
  projectDir = ./.;
  overrides = [
    pkgs.poetry2nix.defaultPoetryOverrides
  ];
}

