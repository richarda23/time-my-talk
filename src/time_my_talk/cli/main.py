"""CLI interface for Time My Talk."""

import time
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from ..core.pace import PaceCalculator
from ..core.script import Script
from ..core.tracker import ProgressTracker
from ..speech.audio import AudioInput
from ..speech.recognizer import SpeechRecognizer


class TalkTimer:
    """Main application for timing presentations."""

    def __init__(self, script_file: str, duration_minutes: float):
        """Initialize the talk timer.

        Args:
            script_file: Path to script file
            duration_minutes: Target duration in minutes
        """
        self.script_file = script_file
        self.duration_minutes = duration_minutes
        self.console = Console()

        # Initialize components
        self.script = None
        self.tracker = None
        self.pace_calculator = None
        self.recognizer = None
        self.audio = None

        # Timing
        self.start_time = None

    def setup(self) -> None:
        """Setup all components."""
        self.console.print("\n[bold cyan]Time My Talk[/bold cyan]\n")

        # Load script
        self.console.print(f"Loading script: {self.script_file}...")
        self.script = Script(self.script_file)
        self.console.print(
            f"✓ Loaded script with {self.script.word_count} words\n",
            style="green",
        )

        # Initialize tracker and pace calculator
        self.tracker = ProgressTracker(self.script)
        self.pace_calculator = PaceCalculator(self.duration_minutes)

        # Initialize speech recognition
        self.console.print("Initializing speech recognition...")
        self.recognizer = SpeechRecognizer()
        self.recognizer.initialize()
        self.console.print("✓ Speech recognition ready\n", style="green")

        # Initialize audio
        self.audio = AudioInput()

    def create_display(self, elapsed: float) -> Panel:
        """Create the display panel.

        Args:
            elapsed: Elapsed time in seconds

        Returns:
            Rich Panel with current status
        """
        # Get current status
        progress_status = self.tracker.get_status()
        pace_status = self.pace_calculator.calculate_pace(
            elapsed, progress_status.percentage
        )

        # Create progress bar
        progress = Progress(
            TextColumn("[bold blue]{task.percentage:.0f}%"),
            BarColumn(bar_width=40),
            TextColumn("{task.completed}/{task.total} words"),
        )
        task = progress.add_task(
            "Progress",
            total=progress_status.total_words,
            completed=progress_status.current_word_index,
        )

        # Create status table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="cyan")
        table.add_column("Value", style="white")

        # Format times
        elapsed_str = self._format_time(elapsed)
        target_str = self._format_time(self.duration_minutes * 60)
        expected_str = f"{pace_status.expected_percentage:.1f}%"

        # Status icon
        if pace_status.is_on_pace:
            status_icon = "✓"
            status_style = "green"
        elif pace_status.seconds_ahead > 0:
            status_icon = "⚡"
            status_style = "yellow"
        else:
            status_icon = "⚠"
            status_style = "red"

        table.add_row("Script:", Path(self.script_file).name)
        table.add_row("Target:", target_str)
        table.add_row("", "")
        table.add_row("Elapsed:", elapsed_str)
        table.add_row("Expected:", expected_str)
        table.add_row(
            "Status:",
            f"[{status_style}]{status_icon} {pace_status.status_text}[/{status_style}]",
        )

        # Add last heard text if available
        if progress_status.last_matched_text:
            last_text = progress_status.last_matched_text
            if len(last_text) > 40:
                last_text = "..." + last_text[-37:]
            table.add_row("", "")
            table.add_row("Last heard:", f'"{last_text}"')

        # Build the panel content
        from rich.console import Group

        content = Group(
            progress,
            "",
            table,
        )

        return Panel(
            content,
            title="[bold]Time My Talk[/bold]",
            border_style="cyan",
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def run(self) -> None:
        """Run the main application loop."""
        self.console.print(
            "[green]Starting in 3 seconds... Get ready to speak![/green]\n"
        )
        time.sleep(3)

        self.start_time = time.time()
        self.audio.start()

        try:
            with Live(
                self.create_display(0),
                console=self.console,
                refresh_per_second=2,
            ) as live:
                # Start recognition loop
                for recognized_text in self.recognizer.recognize_stream(self.audio):
                    # Update tracker with recognized text
                    self.tracker.update(recognized_text)

                    # Update display
                    elapsed = time.time() - self.start_time
                    live.update(self.create_display(elapsed))

                    # Check if finished
                    progress = self.tracker.get_status()
                    if progress.percentage >= 99.0:
                        break

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Stopped by user[/yellow]")
        finally:
            self.cleanup()

        # Show final summary
        self.show_summary()

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.audio:
            self.audio.cleanup()

    def show_summary(self) -> None:
        """Show final summary."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        progress = self.tracker.get_status()
        pace = self.pace_calculator.calculate_pace(elapsed, progress.percentage)

        self.console.print("\n[bold]Session Complete![/bold]\n")

        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Label", style="cyan")
        summary_table.add_column("Value", style="white")

        summary_table.add_row("Final progress:", f"{progress.percentage:.1f}%")
        summary_table.add_row("Time taken:", self._format_time(elapsed))
        summary_table.add_row("Target time:", self._format_time(self.duration_minutes * 60))
        summary_table.add_row("Final status:", pace.status_text)

        self.console.print(summary_table)
        self.console.print()


@click.command()
@click.argument("script_file", type=click.Path(exists=True))
@click.option(
    "--duration",
    "-d",
    type=float,
    required=True,
    help="Target duration in minutes",
)
def main(script_file: str, duration: float) -> None:
    """Time your presentation with real-time speech recognition.

    SCRIPT_FILE: Path to your presentation script text file
    """
    try:
        timer = TalkTimer(script_file, duration)
        timer.setup()
        timer.run()
    except FileNotFoundError as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise click.Abort()


if __name__ == "__main__":
    main()
