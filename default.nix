{ pkgs ? import <nixpkgs> {} }:
let
  pythonEnvironment = pkgs.python39.withPackages (ps: [
    ps.bluepy
  ]);
in pkgs.mkShell {

  shellHook = ''
    echo "LOL"
  '';

  packages = [
    pythonEnvironment
  ];
}
