import typer

from beneuro_data.cli.rename_videos_command import rename_videos
from beneuro_data.cli.query_commands import list_today
from beneuro_data.cli.upload_commands import upload_last, upload_session
from beneuro_data.cli.validate_commands import (
    validate_today,
    validate_session,
    validate_sessions,
    validate_last,
)
from beneuro_data.cli.config_commands import show_config, check_config, init
from beneuro_data.cli.self_update_command import self_update


app = typer.Typer()

app.command()(self_update)

app.command()(show_config)
app.command()(check_config)
app.command()(init)

app.command()(list_today)

app.command()(validate_today)
app.command()(validate_session)
app.command()(validate_sessions)
app.command()(validate_last)

app.command()(upload_last)
app.command()(upload_session)
app.command()(rename_videos)


if __name__ == "__main__":
    app()
