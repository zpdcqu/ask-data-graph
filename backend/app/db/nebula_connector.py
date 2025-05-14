from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config as NebulaConfig
from app.core.config import settings
from contextlib import contextmanager

# Global connection pool
connection_pool = None

def init_nebula_connection_pool():
    global connection_pool
    if connection_pool:
        return

    nebula_config = NebulaConfig()
    nebula_config.max_connection_pool_size = 10 # Configure as needed
    try:
        connection_pool = ConnectionPool()
        # settings.NEBULA_GRAPH_HOST might be a comma-separated list of addresses
        addresses = [(host.strip(), settings.NEBULA_GRAPH_PORT) for host in settings.NEBULA_GRAPH_HOST.split(',')]
        connection_pool.init(addresses, nebula_config)
        print("Nebula Graph connection pool initialized.")
    except Exception as e:
        print(f"Failed to initialize Nebula Graph connection pool: {e}")
        connection_pool = None # Ensure it's None if init fails

@contextmanager
def get_nebula_session(space_name: str = settings.NEBULA_SPACE_NAME):
    global connection_pool
    if not connection_pool:
        # Attempt to initialize if not already done, or raise an error
        init_nebula_connection_pool()
        if not connection_pool:
            raise ConnectionError("Nebula Graph connection pool is not initialized.")

    session = None
    try:
        session = connection_pool.get_session(settings.NEBULA_USER, settings.NEBULA_PASSWORD)
        if space_name:
            session.execute(f"USE `{space_name}`;") # Ensure backticks for space names if they contain special chars
        yield session
    except Exception as e:
        # Log the exception appropriately
        print(f"Nebula session error: {e}")
        raise # Re-raise the exception to be handled by the caller
    finally:
        if session:
            session.release()

async def close_nebula_connection_pool():
    global connection_pool
    if connection_pool:
        connection_pool.close()
        print("Nebula Graph connection pool closed.")
        connection_pool = None

# Example usage (primarily for testing, actual queries will be in services)
async def test_nebula_connection():
    try:
        with get_nebula_session() as session:
            resp = session.execute_json("SHOW SPACES;") # execute_json returns a JSON string
            print(f"Nebula SHOW SPACES response: {resp}")
            return True, resp
    except Exception as e:
        print(f"Nebula connection test failed: {e}")
        return False, str(e) 