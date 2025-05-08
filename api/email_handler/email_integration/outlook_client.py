import  os
from ms_graph import get_access_token, MS_GRAPH_BASE_URL
from dotenv import  load_dotenv

load_dotenv()

APPLICATION_ID = os.getenv("APPLICATION_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = ['User.Read', 'Mail.ReadWrite', 'Mail.Send']


get_access_token(application_id=APPLICATION_ID, client_secret=CLIENT_SECRET, scopes=SCOPES)
