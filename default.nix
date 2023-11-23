{ pkgs ? import <nixpkgs> { } }:
let
  poetry2nix = pkgs.callPackage (pkgs.fetchFromGitHub {
    owner = "nix-community";
    repo = "poetry2nix";
    rev = "2023.11.233109";
    hash = "sha256-jOcL6cQhUGmnZT8KGHiwdEi7xSbdheb0MgDE8cf1rVM=";
  }) {};
in poetry2nix.mkPoetryApplication {
  name = "ble-thermometer-scan";
  version = "0.2";
  projectDir = ./.;
  overrides = [
    poetry2nix.defaultPoetryOverrides
  ];
}

