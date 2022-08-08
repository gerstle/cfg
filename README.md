# dotfile management

Uses the bare repo approach outlined here: https://www.atlassian.com/git/tutorials/dotfiles

# setup

1. `brew install romkatv/powerlevel10k/powerlevel10k`
2. `brew install zsh-autosuggestions`
3. `brew install zsh-completions`
4. `brew install asdf`
5. `echo ".cfg" >> .gitignore`
6. `git clone --bare git@github.com:gerstle/cfg.git $HOME/.cfg`
7. `alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'`
8. `config checkout`
9. delete any conflicts, re-run checkout
10. `config config --local status.showUntrackedFiles no`

