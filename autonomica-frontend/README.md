# Autonomica Marketing AI Dashboard

A cutting-edge marketing automation platform powered by OWL (Optimized Workflow Language) and CAMEL multi-agent systems. This Next.js frontend provides an intelligent chat interface for marketing strategy, content creation, SEO analysis, and campaign planning.

## 🚀 Features

- **AI-Powered Chat Interface** - Real-time streaming chat with marketing AI assistant
- **Modern UI/UX** - Built with Next.js 14, TypeScript, and Tailwind CSS
- **Streaming Responses** - Real-time AI responses using Vercel AI SDK
- **Marketing Focus** - Specialized prompts for marketing strategy, content, and analytics
- **Responsive Design** - Works perfectly on desktop and mobile devices
- **Type-Safe** - Full TypeScript integration throughout

## 🛠️ Tech Stack

- **Frontend**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **AI Integration**: Vercel AI SDK + OpenAI
- **Components**: React 18 with custom chat components
- **Markdown**: React Markdown for rich AI responses

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- OpenAI API key

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
npm install
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env.local

# Add your OpenAI API key to .env.local
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000 in your browser
```

### 4. Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   ├── chat/          # Chat streaming endpoint
│   │   └── health/        # Health check endpoint
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Homepage with chat interface
├── components/            # React components
│   ├── chat-input.tsx     # Chat input component
│   ├── chat-messages.tsx  # Chat messages display
│   ├── chat-container.tsx # Basic chat container
│   ├── chat-container-ai.tsx # AI-powered chat container
│   ├── layout.tsx         # App layout component
│   └── index.ts           # Component exports
├── lib/                   # Utilities and hooks
│   ├── config.ts          # Environment configuration
│   ├── use-chat.ts        # Custom chat hook with AI SDK
│   └── utils.ts           # Utility functions
└── types/                 # TypeScript type definitions
    └── chat.ts            # Chat-related types
```

## 🔧 API Endpoints

### POST /api/chat
Streaming chat endpoint that processes user messages and returns AI responses.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Help me create a marketing strategy"}
  ]
}
```

**Response:** Streaming text response

### GET /api/health
Health check endpoint to verify API status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "environment": "development",
  "services": {
    "openai": "configured",
    "api": "http://localhost:3000"
  }
}
```

## 🎯 Usage Examples

The AI assistant specializes in marketing topics:

- **Marketing Strategy**: "Help me create a marketing strategy for a new SaaS product"
- **Content Creation**: "Write a blog post about AI in marketing"
- **SEO Analysis**: "What are the best keywords for content marketing in 2024?"
- **Social Media**: "Create a social media content calendar for a tech startup"
- **Analytics**: "How do I measure the ROI of my content marketing efforts?"

## 🔐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for chat functionality | Yes | - |
| `NEXT_PUBLIC_API_URL` | Public API URL for frontend | No | `http://localhost:3000` |
| `API_URL` | Internal API URL for server-side calls | No | `http://localhost:3000` |
| `NODE_ENV` | Environment (development/production) | No | `development` |

## 🚀 Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy automatically

### Other Platforms

The application can be deployed to any platform that supports Next.js:

- Netlify
- Railway
- AWS Amplify
- Digital Ocean App Platform

## 🧪 Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm start           # Start production server
npm run lint        # Run ESLint
npm run lint:fix    # Fix ESLint errors
```

### Adding New Features

1. **New Components**: Add to `src/components/`
2. **API Routes**: Add to `src/app/api/`
3. **Types**: Add to `src/types/`
4. **Utilities**: Add to `src/lib/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Autonomica ecosystem. See the main repository for license information.

## 🆘 Support

For support and questions:

- Check the [Issues](../../issues) section
- Review the [Documentation](../../README.md)
- Contact the development team

---

**Built with ❤️ for the future of AI-powered marketing automation**
