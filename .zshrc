# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

source ~/powerlevel10k/powerlevel10k.zsh-theme
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh

autoload -Uz compinit
compinit
[[ $commands[kubectl] ]] && source <(kubectl completion zsh)

[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

export PATH=$HOME:/usr/local/sbin:~/bin/:~/src/pulsara/devops/deployment/bin:/usr/local/opt/terraform@0.13/bin:$PATH
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"

setopt HIST_IGNORE_DUPS
setopt APPENDHISTORY     #Append history to the history file (no overwriting)
# setopt SHAREHISTORY      #Share history across terminals
setopt INCAPPENDHISTORY  #Immediately append to the history file, not just when a term is killed
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000

ZSH_AUTOSUGGEST_HISTORY_IGNORE=('cd *')

source ~/.alias

# asdf and SDK stuff
. /opt/homebrew/opt/asdf/libexec/asdf.sh

# Use vim cli mode
bindkey -v
export KEYTIMEOUT=1
set editing-mode vi
set blink-matching-paren on

# home/end fixes for mac & iterm2
bindkey '^[[H' beginning-of-line
bindkey -M vicmd '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey -M vicmd '^[[F' beginning-of-line

bindkey '^P' up-history
bindkey '^N' down-history

# backspace and ^h working even after
# returning from command mode
bindkey '^?' backward-delete-char
bindkey '^h' backward-delete-char

# ctrl-w removed word backwards
bindkey '^w' backward-kill-word

# ctrl-r starts searching history backward
bindkey '^r' history-incremental-search-backward

# shift-<direction> for moving up and down in command history when you have multi-line commands
bindkey -M vicmd 'K' up-history
bindkey -M vicmd 'J' up-history

test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"

export HOMEBREW_GITHUB_API_TOKEN=$(cat ~/.config/gh/pat)
export GREP_OPTIONS="--color=always"


# Created by `pipx` on 2022-10-11 20:00:33
export PATH="$PATH:/Users/caseygerstle/.local/bin"
. ~/.asdf/plugins/java/set-java-home.zsh

### MANAGED BY RANCHER DESKTOP START (DO NOT EDIT)
export PATH="/Users/caseygerstle/.rd/bin:$PATH"
### MANAGED BY RANCHER DESKTOP END (DO NOT EDIT)

export LIQUIBASE_HOME=/opt/homebrew/opt/liquibase/libexec
export _JAVA_OPTIONS="-Djava.net.preferIPv4Stack=true"
