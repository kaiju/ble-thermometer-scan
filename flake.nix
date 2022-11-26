{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }: (
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in rec {
        packages.ble-thermometer-scan = import ./default.nix { inherit pkgs; };
        defaultPackage = packages.ble-thermometer-scan;
        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.poetry ];
          inputsFrom = builtins.attrValues self.packages.${system};
        };
      }
    )
  ) // {

    overlay = (final: prev: { ble-thermometer-scan = self.packages.${prev.system}.ble-thermometer-scan; });

  };

}
