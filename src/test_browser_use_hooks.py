import allure
from datetime import datetime
from pathlib import Path
from browser_use import Agent
import shutil
import re
import os

async def end_step_hook(agent: Agent, steps_dir: str | Path) -> None:
    page = await agent.browser_session.get_current_page()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    step_number = agent.state.n_steps + 1

    step_name = f"Step {step_number}"
    if agent.state.history.history:
        current_history = agent.state.history.history[-1]
        if current_history.model_output and current_history.model_output.action:
            action_data = current_history.model_output.action[0].model_dump(exclude_unset=True)
            action_name = next(iter(action_data.keys())) if action_data else 'unknown'
            step_name = f"Step {step_number}: {action_name} ({timestamp})"

    with allure.step(step_name):
        screenshot_path = Path(steps_dir) / f"step_{step_number}_screenshot.png"
        await page.screenshot(path=str(screenshot_path),full_page=False)
        allure.attach.file(str(screenshot_path), name="Screenshot", attachment_type=allure.attachment_type.PNG)

        if agent.state.history.history:
            current_history = agent.state.history.history[-1]
            if current_history.model_output:
                action_info = [
                    f"Timestamp: {timestamp}",
                    f"Step Number: {step_number}",
                    f"Current URL: {page.url}",
                    f"Page Title: {page.title}"
                ]
                if current_history.model_output.current_state:
                    state = current_history.model_output.current_state
                    action_info.extend([
                        "\nCurrent State:",
                        f"Evaluation: {state.evaluation_previous_goal}",
                        f"Memory: {state.memory}",
                        f"Next Goal: {state.next_goal}"
                    ])
                if current_history.model_output.action:
                    action_info.append("\nCurrent Actions:")
                    for i, action in enumerate(current_history.model_output.action):
                        action_data = action.model_dump(exclude_unset=True)
                        action_name = next(iter(action_data.keys())) if action_data else 'unknown'
                        action_info.append(f"Action {i+1}: {action_name} - {action_data.get(action_name, {})}")
                if agent.state.last_result:
                    action_info.append("\nAction Results:")
                    for i, result in enumerate(agent.state.last_result):
                        print(f"Step {step_number}: {result}")
                        if result.error:
                            action_info.append(f"Result {i+1}: ❌ Error - {result.error}")
                        else:
                            action_info.append(f"Result {i+1}: ✅ Success - {result.extracted_content}")
                            # Check if the result is about saving a PDF
                            if isinstance(result.extracted_content, str):
                                pdf_match = re.match(r"Saving page (.*?) as PDF to (.*?\.pdf)", result.extracted_content)
                                if pdf_match:
                                    # Get the project root directory
                                    project_root = Path(os.getcwd())
                                    # Get the PDF path relative to project root
                                    pdf_path = project_root / pdf_match.group(2).lstrip('./')
                                    if pdf_path.exists():
                                        # Extract original PDF name and create new path
                                        original_pdf_name = pdf_path.name
                                        new_pdf_path = Path(steps_dir) / f"step_{step_number}_{original_pdf_name}"
                                        try:
                                            shutil.move(str(pdf_path), str(new_pdf_path))
                                            # Attach PDF to allure report
                                            allure.attach.file(
                                                str(new_pdf_path),
                                                name=f"Page PDF - Step {step_number} - {original_pdf_name}",
                                                attachment_type=allure.attachment_type.PDF
                                            )
                                        except Exception as e:
                                            action_info.append(f"❌ Failed to move PDF file: {str(e)}")
                action_info_path = Path(steps_dir) / f"step_{step_number}_info.txt"
                with open(action_info_path, "w") as f:
                    f.write("\n".join(action_info))
                allure.attach(
                    "\n".join(action_info),
                    name="Action Information",
                    attachment_type=allure.attachment_type.TEXT
                )