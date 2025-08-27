import os
from flask import Flask, request, render_template_string
from opensearchpy import OpenSearch

app = Flask(__name__)

# OpenSearch connection
host = os.environ.get('OPENSEARCH_HOST', 'localhost')
port = int(os.environ.get('OPENSEARCH_PORT', 9200))
client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_auth=None,
    use_ssl=False,
    verify_certs=False,
    ssl_show_warn=False
)

# Index name
index_name = 'test_index'

# Create index if not exists
mapping = {
    'mappings': {
        'properties': {
            'title': {'type': 'text'},
            'content': {'type': 'text'},
            'content_type': {'type': 'keyword'}
        }
    }
}

if not client.indices.exists(index=index_name):
    client.indices.create(index=index_name, body=mapping)
    
    # Load sample data
    documents = [
        {'title': 'Document One', 'content': 'This is the content for the first document. It has some text.', 'content_type': 'type1'},
        {'title': 'Document Two', 'content': 'Content for the second document goes here. More text.', 'content_type': 'type2'},
        {'title': 'Document Three', 'content': 'Third document content. This is random text.', 'content_type': 'type3'},
        {'title': 'Document Four', 'content': 'Fourth document with some content. Hello world.', 'content_type': 'type4'},
        {'title': 'Document Five', 'content': 'Fifth document content. Testing search.', 'content_type': 'type1'}
    ]
    
    for i, doc in enumerate(documents):
        client.index(index=index_name, id=i+1, body=doc)

# Content types
content_types = ['type1', 'type2', 'type3', 'type4']

# Search function
def search(keyword, content_type=None):
    query = {
        'query': {
            'multi_match': {
                'query': keyword,
                'fields': ['title', 'content']
            }
        },
        'size': 10
    }
    
    if content_type:
        query['query'] = {
            'bool': {
                'must': query['query'],
                'filter': {
                    'term': {'content_type': content_type}
                }
            }
        }
    
    response = client.search(index=index_name, body=query)
    
    results = []
    for hit in response['hits']['hits']:
        snippet = hit['_source']['content'][:50]
        results.append({
            'title': hit['_source']['title'],
            'snippet': snippet
        })
    return results

# Web routes
@app.route('/', methods=['GET', 'POST'])
def index():
    keyword = request.form.get('keyword', '')
    content_type = request.form.get('content_type', None)
    results = []
    if keyword:
        results = search(keyword, content_type)
    
    # HTML form
    html = '''
    <form method="post">
        <input type="text" name="keyword" value="{{ keyword }}" placeholder="Search keyword">
        <br>
        Content Type:
        {% for typ in content_types %}
            <input type="radio" name="content_type" value="{{ typ }}" {% if typ == selected_type %}checked{% endif %}> {{ typ }}
        {% endfor %}
        <br>
        <button type="submit">Search</button>
    </form>
    <h2>Results:</h2>
    <ul>
    {% for res in results %}
        <li><b>{{ res.title }}</b>: {{ res.snippet }}</li>
    {% endfor %}
    </ul>
    '''
    
    return render_template_string(html, keyword=keyword, selected_type=content_type, content_types=content_types, results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)