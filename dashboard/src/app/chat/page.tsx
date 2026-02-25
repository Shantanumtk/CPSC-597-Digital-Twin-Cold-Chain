import ChatWidget from "@/components/ChatWidget";

export default function ChatPage() {
  return (
    <div className="p-4">
      <ChatWidget
        agent="query"
        title="🔍 Cold Chain Query Agent"
        placeholder="Ask about your cold chain data..."
        suggestions={[
          "Which assets are critical right now?",
          "Why is truck-01 temperature rising?",
          "Show me all breaches in the last 24 hours",
          "Compare SLA compliance across all trucks",
          "What is the current state of cold-room-site-1-room-1?",
        ]}
      />
    </div>
  );
}
