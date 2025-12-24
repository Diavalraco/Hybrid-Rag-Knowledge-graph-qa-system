#!/bin/bash
# Test Document Ingestion

echo "Creating test document..."
cat > /tmp/test_doc.txt << 'EOF'
John Smith works at Tech Corp as the Engineering Manager. Tech Corp is a technology company located in San Francisco, California. The company specializes in developing AI products and machine learning solutions.

John Smith manages a team of 15 engineers. The Engineering team at Tech Corp is responsible for developing the company's flagship AI platform. The team has expertise in Python, machine learning frameworks, and cloud infrastructure.

Sarah Johnson is the CEO of Tech Corp. She has been leading the company since 2018. Sarah Johnson reports to the board of directors and works closely with John Smith on product strategy.

Tech Corp was founded in 2015 and has raised over $50 million in funding. The company's main office is located at 123 Innovation Drive, San Francisco.
EOF

echo "Encoding document to base64..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    BASE64_CONTENT=$(base64 -i /tmp/test_doc.txt)
else
    BASE64_CONTENT=$(base64 -w 0 /tmp/test_doc.txt)
fi

echo "Ingesting document..."
curl -X POST "http://localhost:8000/ingest/document" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_name\": \"test_doc.txt\",
    \"file_content\": \"$BASE64_CONTENT\",
    \"file_type\": \"txt\"
  }" | python3 -m json.tool

echo -e "\n\nDocument ingested successfully!"

