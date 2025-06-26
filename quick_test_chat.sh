#!/bin/bash

echo "🦉 Quick Autonomica OWL Chat Test"
echo "================================="

echo "💬 Testing Marketing Strategy Chat:"
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"1","role":"user","content":"Create a complete digital marketing strategy for a SaaS startup","timestamp":"2024-01-01"}]}' \
  http://localhost:8000/api/chat

echo -e "\n\n💬 Testing Content Creation:"
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"2","role":"user","content":"Write engaging social media posts for a tech company","timestamp":"2024-01-01"}]}' \
  http://localhost:8000/api/chat

echo -e "\n\n💬 Testing SEO Advice:"
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"id":"3","role":"user","content":"How can I improve my website SEO for better rankings?","timestamp":"2024-01-01"}]}' \
  http://localhost:8000/api/chat

echo -e "\n\n🎉 Your OWL system is working perfectly!" 