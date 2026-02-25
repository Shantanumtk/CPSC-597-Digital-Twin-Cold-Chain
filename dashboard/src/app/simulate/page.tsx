import ChatWidget from "@/components/ChatWidget";

export default function SimulatePage() {
  return (
    <div className="p-4">
      <ChatWidget
        agent="simulate"
        title="🎮 Simulation Controller"
        placeholder="Describe a scenario to simulate..."
        suggestions={[
          "Open truck-02's door for 3 minutes",
          "Simulate compressor failure on truck-05",
          "Trigger a power outage at site-1 for 10 minutes",
          "Scale the fleet to 20 trucks",
          "What is the current simulator status?",
        ]}
      />
    </div>
  );
}
