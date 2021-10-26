{ pkgs ? import <nixpkgs> {} }:
let
  pythonEnvironment = pkgs.python39.withPackages (ps: [
    ps.bluepy
    ps.pip
    ps.requests
    ps.bleak
    ps.asyncio-mqtt
  ]);
in pkgs.mkShell {
  packages = [
    pythonEnvironment
  ];
}
