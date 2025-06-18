import pytest
import allure
from typing import Tuple
from browser_use import AgentHistoryList, ActionResult, Controller
from src.test_browser_use_base import BaseBrowserTest
from pydantic import BaseModel

TEST_TASK: str = f"""
DO NOT MERGE MY STEPS!!!
1. Navigate to https://www.spacex.com/
2. Save the current page as a PDF file
3. Click on 'FALCON 9' in the navigation bar, scroll down 500px
3. Scroll to 'stats' section and then Extracte Falcon 9 stats of COMPLETED MISSIONS, TOTAL LANDINGS, TOTAL REFLIGHTS
5. Scroll down 6000px to the bottom of the page 
6. Scroll up 1500px 
7. Scroll to 'engines'section and wait for 1s
8. call function extract_merlin_engine_info to Extract MERLIN ENGINE DETAILS for SEA LEVE and VACUUM from its data table. 
9. Scroll up 6000px to the top of the page
10. Click on 'STARLINK' in the navigation bar then switch to the new tab
12. Save the new tab page as a PDF file
"""


class EngineInfo(BaseModel):
    """
    Represents technical details of an engine.

    Attributes:
        thrust (str): The thrust of the engine.
        propellant (str): The type of propellant used by the engine.
    """
    thrust: str
    propellant: str


class MerlinEngine(BaseModel):
    """
    Represents the Merlin engine specifications for SEA LEVEL and VACUUM.

    Attributes:
        sea_level (EngineInfo): Technical details of the engine at sea level.
        vacuum (EngineInfo): Technical details of the engine in vacuum conditions.
    """
    sea_level: EngineInfo
    vacuum: EngineInfo


class Stats(BaseModel):
    """
    Represents Falcon 9 statistics.

    Attributes:
        completed_missions (int): Number of completed missions.
        total_landings (int): Total number of landings.
        total_reflights (int): Total number of reflights.
    """
    completed_missions: int
    total_landings: int
    total_reflights: int


class Falcon9Summary(BaseModel):
    """
    Represents a summary of Falcon 9 data, including statistics and engine details.

    Attributes:
        stats (Stats): Falcon 9 statistics.
        engine (MerlinEngine): Merlin engine specifications.
    """
    stats: Stats
    engine: MerlinEngine


controller = Controller(output_model=Falcon9Summary)


@controller.registry.action('Extracte Falcon 9 stats of COMPLETED MISSIONS, TOTAL LANDINGS, TOTAL REFLIGHTS', param_model=Stats)
async def extract_falcon_9_stats(params: Stats):
    """
    Custom action to extract Falcon 9 statistics.

    Args:
        params (Stats): The statistics to be extracted.

    Returns:
        ActionResult: The result of the extraction, including the extracted content.
    """
    print(f"Custom action: extract_falcon_9_stats: {params}")
    print(f"Custom action: extract_falcon_9_stats: {params.model_dump_json()}")
    result = ActionResult(is_done=False, success=True, include_in_memory=True,
                          extracted_content=params.model_dump_json())
    return result


@controller.registry.action('Extract MERLIN ENGINE technical details and specifications for SEA LEVEL and VACUUM', param_model=MerlinEngine)
async def extract_merlin_engine_info(params: MerlinEngine):
    """
    Custom action to extract Merlin engine technical details and specifications.

    Args:
        params (MerlinEngine): The engine details to be extracted.

    Returns:
        ActionResult: The result of the extraction, including the extracted content.
    """
    print(f"Custom action: extract_merlin_engine_info: {params}")
    print(
        f"Custom action: extract_merlin_engine_info: {params.model_dump_json()}")

    result = ActionResult(is_done=False, success=True, include_in_memory=True,
                          extracted_content=params.model_dump_json())
    return result


def verify_agent_result(history: AgentHistoryList) -> Tuple[bool, str, str]:
    """
    Verifies if the search result contains the expected text.

    Args:
        history (AgentHistoryList): The history of agent actions.

    Returns:
        bool: True if the verification is successful, False otherwise.
    """

    is_valid = True
    error_message = None
    agent_result = None

    _result: str = history.final_result()
    agent_result = _result
    summary: Falcon9Summary = Falcon9Summary.model_validate_json(_result)
    print(f"verify_agent_result: {summary}")

    if summary.engine.vacuum.thrust != '000':
        msg = f"Vacuum thrust is '{summary.engine.vacuum.thrust}', expected '000'."
        allure.attach(msg, name="vacuum_thrust_mismatch",
                      attachment_type=allure.attachment_type.TEXT)
        error_message = msg
        is_valid = False

    return is_valid, agent_result, error_message,


message_context = """
You are an automated web testing assistant that performs interactions and extracts data using custom actions.

CRITICAL INSTRUCTIONS:
1. After completing web interactions (navigation, clicks, form submissions), you MUST call appropriate actions to verify or extract information.

2. Available Custom Actions:
   - extract_falcon_9_stats: Extract Falcon 9 COMPLETED MISSIONS, TOTAL LANDINGS, TOTAL REFLIGHTS statistics
   - extract_merlin_engine_info: Extracted VACUUM Merlin engine details and Extracted SEA LEVEL Merlin engine details

3. When to Call Actions:
   - IMMEDIATELY after navigating to pages containing relevant data
   - AFTER page content has fully loaded and is visible
   - WHEN you encounter Falcon 9 statistics
   - WHEN you encounter Merlin engine details
   - AFTER any interaction that might update the displayed data

4. Action Calling Pattern:
   - Navigate to target page
   - Wait for content to load
   - Locate relevant information on page
   - Call appropriate extraction action
   - Continue to next step

5. Important:
   - Don't just describe what you see - EXTRACT the data using custom actions
   - Call extraction actions whenever you find matching data
   - Verify extraction was successful before proceeding

EXAMPLE WORKFLOW:
1. Extracte Falcon 9 stats of COMPLETED MISSIONS, TOTAL LANDINGS, TOTAL REFLIGHTS → MUST call extract_falcon_9_stats
2. Extracted SEA LEVEL Merlin engine details → MUST call extract_merlin_engine_info
3. Extracted VACUUM Merlin engine details → MUST call extract_merlin_engine_info
"""


@allure.epic("Browser-Use Testing")
@allure.feature("SpaceX")
@allure.story("Browser-Use Agent with Custom Instructions")
@allure.severity(allure.severity_level.NORMAL)
class TestSpaceX:
    """
    Test class for SpaceX browser-use testing.

    Attributes:
        None

    Methods:
        test_spacex(): Executes the SpaceX test using the provided task and controller.
    """
    @pytest.mark.asyncio
    async def test_spacex(self) -> None:
        """Test with explicit screenshot instructions for the agent."""
        test = BaseBrowserTest(
            task=TEST_TASK,
            controller=controller,
            message_context=message_context,
            verify_function=verify_agent_result
        )
        await test.run_test()
