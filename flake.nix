{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
    }:
    (flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # uv workspace
        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

        # workspace overlay that we'll apply to the python set
        workspaceOverlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

        # python set w/ our workspace overlay
        pythonSet =
          (pkgs.callPackage pyproject-nix.build.packages {
            python = pkgs.python313;
          }).overrideScope
            (
              nixpkgs.lib.composeManyExtensions [
                pyproject-build-systems.overlays.wheel
                workspaceOverlay
              ]
            );
      in
      rec {

        packages.ble-thermometer-scan = pythonSet.mkVirtualEnv "ble-thermometer-scan-env" workspace.deps.default;
        defaultPackage = packages.ble-thermometer-scan;

        devShell =
          let
            editableOverlay = workspace.mkEditablePyprojectOverlay {
              root = "$REPO_ROOT";
            };
            editablePythonset = pythonSet.overrideScope editableOverlay;
            virtualenv = editablePythonset.mkVirtualEnv "ble-thermometer-scan-dev-env" workspace.deps.all;
          in
          pkgs.mkShell {
            packages = with pkgs; [
              virtualenv
              uv
              ruff
            ];

            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = editablePythonset.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };

      }
    ))
    // {

      overlay = (
        final: prev: { ble-thermometer-scan = self.packages.${prev.system}.ble-thermometer-scan; }
      );

    };

}
