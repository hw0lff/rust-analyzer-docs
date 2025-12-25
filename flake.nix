{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs =
    { flake-utils
    , nixpkgs
    , ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        overlays = [ ];
        pkgs = import nixpkgs { inherit system overlays; };
      in
      {
        devShells.default = with pkgs; mkShell rec {
          buildInputs = [
          ];
          nativeBuildInputs = [
            python3
            pandoc
            bash
            git
            just
          ];
          LD_LIBRARY_PATH = (nixpkgs.lib.makeLibraryPath buildInputs);
          shellHook = ''
          '';
        };
      }
    );
}
