import typer

from agentql._cli._commands import doctor_command, init_command

app = typer.Typer(no_args_is_help=True)
app.command()(init_command.init)
app.command()(doctor_command.doctor)


if __name__ == "__main__":
    app()
