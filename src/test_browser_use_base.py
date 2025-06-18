import pytest
import allure
import json
import os
from dotenv import load_dotenv
from browser_use import BrowserSession, BrowserProfile, Agent, AgentHistoryList, Controller
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from .test_utils import attach_agent_history_to_allure, attach_gifs_to_allure, setup_directories, save_agent_history, attach_logs_to_allure
from .test_browser_use_hooks import end_step_hook
from pathlib import Path
from typing import Callable, Optional, Tuple

load_dotenv()

# gpt > gemini > claude
# gpt-4o gpt-4o-mini gpt-4.1 gpt-4.1-mini
# gemini-2.5-pro-preview-05-06  gemini-2.0-flash-thinking-exp gemini-2.0-flash-exp
# claude-sonnet-4-20250514 claude-opus-4-20250514
# claude-3-7-sonnet-20250219 claude-3-7-sonnet-thinking claude-3-opus-20240229

CHAT_LLM_MODEL = "gpt-4.1"
# CHAT_LLM_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
# CHAT_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
# CHAT_LLM_MODEL = "gpt-4.1"
CHAT_LLM_ENDPOINT = os.getenv("CLOUDAPI_ENDPOINT")
CHAT_LLM_API_KEY = os.getenv("CLOUDAPI_API_KEY")

PLANNER_LLM_MODEL = "gemini-2.0-flash-exp"
# PLANNER_LLM_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
# PLANNER_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
# PLANNER_LLM_MODEL = "claude-sonnet-4-20250514"
PLANNER_LLM_ENDPOINT = os.getenv("CLOUDAPI_ENDPOINT")
PLANNER_LLM_API_KEY = os.getenv("CLOUDAPI_API_KEY")

# Default directories for test artifacts (relative to project root)
DEFAULT_LOGS_DIR: str = "logs/"
DEFAULT_STEPS_DIR: str = "steps/"


class BaseBrowserTest:
    def __init__(
        self,
        task: str,
        verify_function: Optional[Callable[[
            AgentHistoryList], Tuple[bool, str, str]]] = None,
        controller: Optional[Controller] = None,
        message_context: Optional[str] = None,
        logs_dir: str = DEFAULT_LOGS_DIR,
        steps_dir: str = DEFAULT_STEPS_DIR,
        storage_state: Optional[str] = None
    ):
        self.task = task
        self.verify_function = verify_function
        self.controller = controller or Controller()
        self.message_context = message_context or "You are an automated web testing assistant. Your primary goal is to perform web interactions and validate results using custom assertion actions."
        # Convert relative paths to absolute paths
        self.logs_dir = logs_dir
        project_root = Path(os.getcwd())
        self.steps_dir = str(project_root / steps_dir)
        self.storage_state = storage_state

    @pytest.mark.asyncio
    async def run_test(self) -> None:
        """Execute the browser test with the provided task and verification function."""
        # Setup directories
        setup_directories(self.logs_dir, self.steps_dir)

        history = None

        browser_profile = BrowserProfile(
            headless=False,
            # storage_state="path/to/storage_state.json",
            wait_for_network_idle_page_load_time=3.0,
            # viewport={"width": 1280, "height": 1100},
            locale='en-US',
            timezone_id="America/New_York",
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
            highlight_elements=True,  # default is True
            # viewport_expansion=500,
            # allowed_domains=['*.google.com', 'http*://*.wikipedia.org'],
            # user_data_dir=None,
        )
        if self.storage_state:
            browser_profile.storage_state = self.storage_state

        browser_session = BrowserSession(
            browser_profile=browser_profile,
            headless=True,  # extra kwargs to the session override the defaults in the profile
        )

        # you can drive a session without the agent / reuse it between agents
        await browser_session.start()
        page = await browser_session.get_current_page()

        initial_actions = [
            {'open_tab': {'url': 'about:blank'}}
        ]

        with allure.step("Create agent with task"):
            chat_llm = ChatOpenAI(
                model=CHAT_LLM_MODEL, base_url=CHAT_LLM_ENDPOINT, api_key=CHAT_LLM_API_KEY)
            planner_llm = ChatOpenAI(
                model=PLANNER_LLM_MODEL, base_url=PLANNER_LLM_ENDPOINT, api_key=PLANNER_LLM_API_KEY)
            agent: Agent = Agent(
                task=self.task,
                llm=chat_llm,
                # optional: default is True
                use_vision=True,
                # optional: default is chat_llm, A LangChain chat model instance used for high-level task planning. Can be a smaller/cheaper model than the main LLM
                planner_llm=planner_llm,
                # optional: Enable/disable vision capabilities for the planner model. Defaults to True
                use_vision_for_planner=True,
                # optional: Number of steps between planning phases. Defaults to 1
                planner_interval=4,
                # optional: Registry of functions the agent can call. Defaults to base Controller. See Custom Functions for details.
                controller=self.controller,
                # optional: Path to save the complete conversation history. Useful for debugging.
                save_conversation_path=self.logs_dir,
                # optional: pass a specific playwright page to start on
                page=page,
                # optional: pass an existing browser session to an agent
                browser_session=browser_session,
                # optional: List of initial actions to run before the main task.
                # initial_actions=initial_actions,
                # optional: Additional information about the task to help the LLM understand the task better.
                message_context=self.message_context,
                # optional: Maximum number of actions to run in a step. Defaults to 10
                max_actions_per_step=3,
                # optional: Enable/disable GIF generation. Defaults to False. Set to True or a string path to save the GIF.
                generate_gif=f"{self.logs_dir}/agent.gif",
            )

        try:
            with allure.step("Execute agent"):
                # Run agent with step hook
                history = await agent.run(on_step_start=lambda agent: end_step_hook(agent, self.steps_dir))

                # Save and attach history
                if history:
                    save_agent_history(history, self.logs_dir)

        except Exception as e:
            history = None
            allure.attach(
                f"Agent failed: {str(e)}",
                name="agent_failure",
                attachment_type=allure.attachment_type.TEXT
            )
            pytest.fail(f"Agent execution failed: {str(e)}")

        finally:
            # Archive logs in a separate step
            with allure.step("Archive Logs"):
                attach_logs_to_allure(self.logs_dir)
                attach_gifs_to_allure(self.logs_dir)
                attach_agent_history_to_allure(self.logs_dir)

            # Verify results after all steps are completed if verify function is provided
            if history and self.verify_function:
                with allure.step("Verify Results"):
                    is_valid, agent_result, error_message = self.verify_function(
                        history)
                    allure.attach(
                        f"Verify result: {is_valid},Agent result: {agent_result}",
                        name="agent_result",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    if not is_valid:
                        pytest.fail(
                            f"Agent result verification failed: {error_message}")
