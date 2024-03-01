# dotfile management

Uses the bare repo approach outlined here: https://www.atlassian.com/git/tutorials/dotfiles

# setup

1. `git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k && echo 'source ~/powerlevel10k/powerlevel10k.zsh-theme' >>~/.zshrc`
2. `brew install zsh-autosuggestions`
3. `brew install zsh-completions`
4. `brew install asdf`
5. `git clone --bare git@github.com:gerstle/cfg.git $HOME/.cfg`
6. `alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'`
7. `config checkout`
8. delete any conflicts, re-run checkout
9. `config config --local status.showUntrackedFiles no`
10. `echo ".cfg" >> .gitignore`
