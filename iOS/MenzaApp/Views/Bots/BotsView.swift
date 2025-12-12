//
//  BotsView.swift
//  MenzaApp
//
//  Bot store and management view
//

import SwiftUI

struct BotsView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @StateObject private var viewModel = BotsViewModel()
    @State private var searchText = ""
    @State private var selectedCategory: BotCategory = .all
    
    enum BotCategory: String, CaseIterable {
        case all = "All"
        case utility = "Utility"
        case fun = "Fun"
        case productivity = "Productivity"
        case crypto = "Crypto"
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                (themeManager.isDarkMode ? Color(hex: "0D0D0D") : Color(hex: "F8F9FA"))
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Category filter
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(BotCategory.allCases, id: \.self) { category in
                                CategoryChip(
                                    title: category.rawValue,
                                    isSelected: selectedCategory == category,
                                    isDarkMode: themeManager.isDarkMode
                                ) {
                                    withAnimation(.spring(response: 0.3)) {
                                        selectedCategory = category
                                    }
                                }
                            }
                        }
                        .padding(.horizontal)
                        .padding(.vertical, 12)
                    }
                    
                    // Bots list
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(filteredBots) { bot in
                                BotCardView(bot: bot, viewModel: viewModel)
                            }
                        }
                        .padding()
                        .padding(.bottom, 80) // Extra padding for tab bar
                    }
                }
            }
            .navigationTitle("Bot Store")
            .searchable(text: $searchText, prompt: "Search bots")
        }
        .task {
            await viewModel.loadBots()
        }
    }
    
    var filteredBots: [Bot] {
        var bots = viewModel.bots
        
        // Filter by category
        if selectedCategory != .all {
            bots = bots.filter { $0.category == selectedCategory.rawValue.lowercased() }
        }
        
        // Filter by search
        if !searchText.isEmpty {
            bots = bots.filter {
                $0.name.localizedCaseInsensitiveContains(searchText) ||
                $0.description.localizedCaseInsensitiveContains(searchText)
            }
        }
        
        return bots
    }
}

// MARK: - Category Chip
struct CategoryChip: View {
    let title: String
    let isSelected: Bool
    let isDarkMode: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .medium)
                .foregroundColor(isSelected ? Color.white : (isDarkMode ? Color.white : Color.black))
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(
                    isSelected ?
                    AnyShapeStyle(
                        LinearGradient(
                            colors: [.menzaPurple, .menzaPink],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    ) :
                    AnyShapeStyle(isDarkMode ? Color.white.opacity(0.08) : Color.white)
                )
                .cornerRadius(20)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(
                            isSelected ? Color.clear : (isDarkMode ? Color.white.opacity(0.1) : Color.gray.opacity(0.2)),
                            lineWidth: 1
                        )
                )
        }
    }
}

// MARK: - Bot Card View
struct BotCardView: View {
    let bot: Bot
    @ObservedObject var viewModel: BotsViewModel
    @EnvironmentObject var themeManager: ThemeManager
    
    var body: some View {
        HStack(spacing: 14) {
            // Bot avatar
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [Color(hex: bot.color), Color(hex: bot.color).opacity(0.7)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 56, height: 56)
                
                Text(bot.emoji)
                    .font(.title2)
            }
            
            // Bot info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(bot.name)
                        .font(.headline)
                        .fontWeight(.semibold)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    
                    if bot.isPremium {
                        Image(systemName: "star.fill")
                            .font(.caption)
                            .foregroundColor(.yellow)
                    }
                }
                
                Text(bot.description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            Spacer()
            
            // Add button
            Button {
                Task {
                    await viewModel.toggleBot(botId: bot.id)
                }
            } label: {
                Text(bot.isAdded ? "Added" : "Add")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(bot.isAdded ? .secondary : Color.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(
                        bot.isAdded ?
                        Color(.systemGray5) :
                        Color.menzaPurple
                    )
                    .cornerRadius(20)
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(themeManager.isDarkMode ? Color.white.opacity(0.06) : Color.white)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(
                    themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.gray.opacity(0.1),
                    lineWidth: 1
                )
        )
    }
}

// MARK: - Bot Model
struct Bot: Identifiable, Equatable {
    let id: String
    let name: String
    let description: String
    let emoji: String
    let color: String
    let category: String
    let isPremium: Bool
    var isAdded: Bool
    
    static func == (lhs: Bot, rhs: Bot) -> Bool {
        lhs.id == rhs.id
    }
}

// MARK: - View Model
@MainActor
class BotsViewModel: ObservableObject {
    @Published var bots: [Bot] = []
    @Published var isLoading = false
    
    private let api = APIService.shared
    
    func loadBots() async {
        isLoading = true
        
        // Load test data
        loadTestData()
        
        // Try to fetch from server
        // (API call would go here)
        
        isLoading = false
    }
    
    func toggleBot(botId: String) async {
        guard let index = bots.firstIndex(where: { $0.id == botId }) else { return }
        
        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        
        // Toggle locally
        bots[index].isAdded.toggle()
        
        // Sync with server
        // (API call would go here)
    }
    
    private func loadTestData() {
        bots = [
            Bot(
                id: "coingecko",
                name: "CoinGecko",
                description: "Real-time cryptocurrency prices, charts, and market data",
                emoji: "🪙",
                color: "8DC63F",
                category: "crypto",
                isPremium: false,
                isAdded: true
            ),
            Bot(
                id: "weather",
                name: "Weather Bot",
                description: "Get weather forecasts for any location worldwide",
                emoji: "🌤️",
                color: "4A90D9",
                category: "utility",
                isPremium: false,
                isAdded: false
            ),
            Bot(
                id: "translator",
                name: "Translator",
                description: "Translate messages between 100+ languages instantly",
                emoji: "🌍",
                color: "7C3AED",
                category: "utility",
                isPremium: false,
                isAdded: true
            ),
            Bot(
                id: "reminder",
                name: "Reminder Bot",
                description: "Set reminders and never forget important tasks",
                emoji: "⏰",
                color: "EC4899",
                category: "productivity",
                isPremium: false,
                isAdded: false
            ),
            Bot(
                id: "meme",
                name: "Meme Generator",
                description: "Create and share hilarious memes with friends",
                emoji: "😂",
                color: "F59E0B",
                category: "fun",
                isPremium: false,
                isAdded: false
            ),
            Bot(
                id: "poll",
                name: "Poll Bot",
                description: "Create polls and surveys for your groups",
                emoji: "📊",
                color: "10B981",
                category: "utility",
                isPremium: false,
                isAdded: false
            ),
            Bot(
                id: "news",
                name: "News Bot",
                description: "Get personalized news from top sources",
                emoji: "📰",
                color: "EF4444",
                category: "utility",
                isPremium: true,
                isAdded: false
            ),
            Bot(
                id: "music",
                name: "Music Bot",
                description: "Share and discover music with friends",
                emoji: "🎵",
                color: "1DB954",
                category: "fun",
                isPremium: true,
                isAdded: false
            ),
            Bot(
                id: "ai_assistant",
                name: "AI Assistant",
                description: "Powered by AI to answer questions and help with tasks",
                emoji: "🤖",
                color: "7C3AED",
                category: "productivity",
                isPremium: true,
                isAdded: false
            ),
            Bot(
                id: "calculator",
                name: "Calculator",
                description: "Perform calculations and unit conversions",
                emoji: "🧮",
                color: "6366F1",
                category: "utility",
                isPremium: false,
                isAdded: false
            )
        ]
    }
}

// MARK: - Preview
struct BotsView_Previews: PreviewProvider {
    static var previews: some View {
        BotsView()
            .environmentObject(ThemeManager())
    }
}


