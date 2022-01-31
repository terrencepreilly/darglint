let
    pkgs = import <nixpkgs> {};
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
        python310
    ];
    nativeBuildInputs = with pkgs; [
    ];
  }
