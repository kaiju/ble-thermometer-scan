{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }: (
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        app = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          # woops, turns out I didn't need bluez, keeping this here anyway for future ref
          #buildInputs = [
          #  (pkgs.python3.withPackages (ps: [ps.bluepy]))
          #];
          overrides = [
            pkgs.poetry2nix.defaultPoetryOverrides
          ];
        };

      in rec {
        packages.ble-thermometer-scanner = app;
        defaultPackage = packages.ble-thermometer-scanner;
        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.poetry ];
          inputsFrom = builtins.attrValues self.packages.${system};
        };
      }
    )
  ) // {

    ble-thermometer-scanner = (final: prev: { ble-thermometer-scanner = self.packages.${prev.system}.ble-thermometer-scanner; });

  };

}
