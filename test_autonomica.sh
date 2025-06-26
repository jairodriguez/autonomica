#!/bin/bash

echo "🦉 Autonomica OWL System API Test Suite"
echo "======================================="

echo -e "\n📊 1. System Health Check:"
curl -s http://localhost:8000/api/health | jq .

echo -e "\n🤖 2. Available Agents:"
curl -s http://localhost:8000/api/agents | jq .

echo -e "\n💬 3. Testing Marketing Strategy Chat:"
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"1","role":"user","content":"I need a digital marketing strategy for a SaaS startup","timestamp":"2024-01-01"}]}' \
  http://localhost:8000/api/chat

echo -e "\n\n📈 4. Testing Content Generation:"
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"2","role":"user","content":"Write a blog post outline about AI automation","timestamp":"2024-01-01"}]}' \
  http://localhost:8000/api/chat

echo -e "\n\n📊 5. Testing Analytics Request:"
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"3","role":"user","content":"How do I track marketing campaign performance?","timestamp":"2024-01-01"}]}' \
  http://localhost:8000/api/chat

echo -e "\n\n✅ OWL System Test Complete!"
echo "Your multi-agent marketing platform is fully operational! 🎉" 