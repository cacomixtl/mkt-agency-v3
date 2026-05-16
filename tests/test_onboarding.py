import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.api.v1.webhook import _check_and_start_onboarding, _handle_onboarding_step
from app.models.user import User

@patch('app.api.v1.webhook.whatsapp_service')
@patch('app.api.v1.webhook.get_session')
async def test_onboarding_flow(mock_get_session, mock_wa):
    # Setup mock AsyncSession
    mock_session = AsyncMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session
    
    # Setup mock user result (None for new user)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result
    
    print("Test 1: New user says Hola")
    is_onboarding, state = await _check_and_start_onboarding("5551234567")
    print(f"Is onboarding: {is_onboarding}")
    print(f"State: {state}")
    mock_wa.send_text_message.assert_called()
    print("Passed Welcome MSG")
    print("-" * 20)

    print("Test 2: User answers Industry")
    # Simulate DB user object existing now
    mock_user = User(phone="5551234567", onboarding_step=1, onboarding_data={})
    mock_result.first.return_value = mock_user
    
    await _handle_onboarding_step("5551234567", "Consultoría Financiera", state)
    print(f"Updated User Step: {mock_user.onboarding_step}")
    assert mock_user.onboarding_step == 2
    print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_onboarding_flow())
