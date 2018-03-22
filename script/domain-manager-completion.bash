#completion script for domain-manager

com_l1()
{
	local cur opts

	cur=${COMP_WORDS[COMP_CWORD]}
	opts="plugin sync"

	COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}

complete -F com_l1 domain-manager
