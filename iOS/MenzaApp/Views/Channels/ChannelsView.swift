//
//  ChannelsView.swift
//  MenzaApp
//
//  Channels discovery and subscription view
//

import SwiftUI

struct ChannelsView: View {
    @StateObject private var viewModel = ChannelsViewModel()
    @State private var searchText = ""
    @State private var selectedFilter: ChannelFilter = .trending
    
    enum ChannelFilter: String, CaseIterable {
        case trending = "Trending"
        case newest = "Newest"
        case popular = "Popular"
        case subscribed = "Subscribed"
    }
    
    var body: some View {
        NavigationStack {
            List {
                // Filter tabs section
                Section {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(ChannelFilter.allCases, id: \.self) { filter in
                                FilterChip(
                                    title: filter.rawValue,
                                    isSelected: selectedFilter == filter
                                ) {
                                    withAnimation {
                                        selectedFilter = filter
                                    }
                                }
                            }
                        }
                    }
                }
                .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                .listRowBackground(Color.clear)
                
                // Channels list
                Section {
                    ForEach(viewModel.channels) { channel in
                        NavigationLink(destination: ChannelDetailView(channel: channel, viewModel: viewModel)) {
                            ChannelCardView(channel: channel, viewModel: viewModel)
                        }
                        .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                        .listRowBackground(Color.clear)
                        .listRowSeparator(.hidden)
                    }
                }
            }
            .listStyle(.plain)
            .navigationTitle("Channels")
            .searchable(text: $searchText, prompt: "Search channels")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    NavigationLink(destination: CreateChannelView(viewModel: viewModel)) {
                        Image(systemName: "plus")
                            .foregroundColor(.menzaPurple)
                    }
                }
            }
        }
        .task {
            await viewModel.loadChannels()
        }
    }
}

// MARK: - Filter Chip
struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? Color.white : .primary)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    isSelected ?
                    AnyShapeStyle(LinearGradient(
                        colors: [.menzaPurple, .menzaPurpleLight],
                        startPoint: .leading,
                        endPoint: .trailing
                    )) :
                    AnyShapeStyle(Color(.systemGray6))
                )
                .cornerRadius(20)
        }
    }
}

// MARK: - Channel Card
struct ChannelCardView: View {
    let channel: Channel
    @ObservedObject var viewModel: ChannelsViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 14) {
                // Avatar with emoji or first letter
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [.menzaPurple, .menzaPink],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 56, height: 56)
                    
                    // Show emoji if name starts with emoji, otherwise show first letter
                    Text(getChannelIcon())
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(Color.white)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(channel.name)
                            .font(.headline)
                            .fontWeight(.semibold)
                        
                        if channel.isVerified {
                            Image(systemName: "checkmark.seal.fill")
                                .foregroundColor(.menzaPurple)
                                .font(.caption)
                        }
                    }
                    
                    Text(formatSubscriberCount(channel.subscriberCount))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Subscribe button
                Button {
                    Task {
                        await viewModel.toggleSubscription(channelId: channel.id)
                    }
                } label: {
                    Text(channel.isSubscribed ? "Subscribed" : "Subscribe")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(channel.isSubscribed ? .secondary : Color.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(
                            channel.isSubscribed ?
                            Color(.systemGray5) :
                            Color.menzaPurple
                        )
                        .cornerRadius(20)
                }
                .buttonStyle(.plain)
            }
            
            if let description = channel.description {
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 10, x: 0, y: 4)
    }
    
    func getChannelIcon() -> String {
        // Check if first character is an emoji
        let name = channel.name
        if let first = name.first, first.isEmoji {
            return String(first)
        }
        // Return first letter uppercase
        return String(name.prefix(1)).uppercased()
    }
    
    func formatSubscriberCount(_ count: Int) -> String {
        if count >= 1000000 {
            return String(format: "%.1fM subscribers", Double(count) / 1000000)
        } else if count >= 1000 {
            return String(format: "%.1fK subscribers", Double(count) / 1000)
        }
        return "\(count) subscribers"
    }
}

// Extension to check if character is emoji
extension Character {
    var isEmoji: Bool {
        guard let scalar = unicodeScalars.first else { return false }
        return scalar.properties.isEmoji && (scalar.value > 0x238C || unicodeScalars.count > 1)
    }
}

// MARK: - Channel Detail View
struct ChannelDetailView: View {
    let channel: Channel
    @ObservedObject var viewModel: ChannelsViewModel
    @State private var showingModeratorSheet = false
    
    private var currentChannel: Channel {
        viewModel.channels.first(where: { $0.id == channel.id }) ?? channel
    }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 12) {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [.menzaPurple, .menzaPink],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 100, height: 100)
                        .overlay(
                            Text(getChannelIcon())
                                .font(.largeTitle)
                                .fontWeight(.bold)
                                .foregroundColor(Color.white)
                        )
                    
                    HStack {
                        Text(currentChannel.name)
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        if currentChannel.isVerified {
                            Image(systemName: "checkmark.seal.fill")
                                .foregroundColor(.menzaPurple)
                        }
                    }
                    
                    Text(formatSubscriberCount(currentChannel.subscriberCount))
                        .foregroundColor(.secondary)
                    
                    // Subscribe button
                    Button {
                        Task {
                            await viewModel.toggleSubscription(channelId: currentChannel.id)
                        }
                    } label: {
                        HStack {
                            Image(systemName: currentChannel.isSubscribed ? "checkmark" : "plus")
                            Text(currentChannel.isSubscribed ? "Subscribed" : "Subscribe")
                        }
                        .font(.headline)
                        .foregroundColor(currentChannel.isSubscribed ? .secondary : Color.white)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 12)
                        .background(
                            currentChannel.isSubscribed ?
                            Color(.systemGray5) :
                            Color.menzaPurple
                        )
                        .cornerRadius(25)
                    }
                    
                    if let description = currentChannel.description {
                        Text(description)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }
                }
                .padding(.top)
                
                // Posts section
                VStack(alignment: .leading, spacing: 8) {
                    Text("Posts")
                        .font(.headline)
                        .padding(.horizontal)
                    
                    if let posts = currentChannel.posts, !posts.isEmpty {
                        LazyVStack(spacing: 16) {
                            ForEach(posts) { post in
                                ChannelPostView(post: post)
                            }
                        }
                        .padding(.horizontal)
                    } else {
                        VStack(spacing: 12) {
                            Image(systemName: "doc.text")
                                .font(.largeTitle)
                                .foregroundColor(.secondary)
                            Text("No posts yet")
                                .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 40)
                    }
                }
            }
        }
        .navigationTitle(currentChannel.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    if isOwner {
                        Button {
                            showingModeratorSheet = true
                        } label: {
                            Label("Manage Moderators", systemImage: "person.badge.shield.checkmark")
                        }
                    }
                    
                    Button {
                        // Share channel
                    } label: {
                        Label("Share Channel", systemImage: "square.and.arrow.up")
                    }
                    
                    if !isOwner {
                        Button(role: .destructive) {
                            // Report channel
                        } label: {
                            Label("Report", systemImage: "exclamationmark.triangle")
                        }
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundColor(.menzaPurple)
                }
            }
        }
        .sheet(isPresented: $showingModeratorSheet) {
            ModeratorManagementView(channelId: currentChannel.id)
        }
    }
    
    var isOwner: Bool {
        let currentUser = UserDefaults.standard.string(forKey: "username") ?? ""
        return currentChannel.owner == currentUser
    }
    
    func getChannelIcon() -> String {
        let name = currentChannel.name
        if let first = name.first, first.isEmoji {
            return String(first)
        }
        return String(name.prefix(1)).uppercased()
    }
    
    func formatSubscriberCount(_ count: Int) -> String {
        if count >= 1000000 {
            return String(format: "%.1fM subscribers", Double(count) / 1000000)
        } else if count >= 1000 {
            return String(format: "%.1fK subscribers", Double(count) / 1000)
        }
        return "\(count) subscribers"
    }
}

// MARK: - Moderator Management View
struct ModeratorManagementView: View {
    let channelId: String
    @Environment(\.dismiss) var dismiss
    @State private var moderators: [String] = []
    @State private var newModeratorUsername = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationStack {
            List {
                Section("Add Moderator") {
                    HStack {
                        TextField("Username", text: $newModeratorUsername)
                            .textInputAutocapitalization(.never)
                        
                        Button("Add") {
                            addModerator()
                        }
                        .disabled(newModeratorUsername.isEmpty || isLoading)
                    }
                    
                    if let error = errorMessage {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
                
                Section("Current Moderators") {
                    if moderators.isEmpty {
                        Text("No moderators yet")
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(moderators, id: \.self) { mod in
                            HStack {
                                Circle()
                                    .fill(Color.menzaPurple.opacity(0.2))
                                    .frame(width: 36, height: 36)
                                    .overlay(
                                        Text(String(mod.prefix(1)).uppercased())
                                            .font(.caption)
                                            .fontWeight(.semibold)
                                            .foregroundColor(.menzaPurple)
                                    )
                                
                                Text(mod)
                                    .font(.body)
                                
                                Spacer()
                                
                                Button {
                                    removeModerator(mod)
                                } label: {
                                    Image(systemName: "minus.circle.fill")
                                        .foregroundColor(.red)
                                }
                            }
                        }
                    }
                }
                
                Section {
                    Text("Moderators can post content to your channel.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Moderators")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
    
    func addModerator() {
        isLoading = true
        errorMessage = nil
        
        // For now, just add locally (server sync would go here)
        moderators.append(newModeratorUsername)
        newModeratorUsername = ""
        isLoading = false
    }
    
    func removeModerator(_ username: String) {
        moderators.removeAll { $0 == username }
    }
}

// MARK: - Channel Post View
struct ChannelPostView: View {
    let post: ChannelPost
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(post.content)
                .font(.body)
            
            HStack {
                Button { } label: {
                    HStack(spacing: 4) {
                        Image(systemName: post.isLiked ? "heart.fill" : "heart")
                            .foregroundColor(post.isLiked ? .red : .secondary)
                        Text("\(post.likes)")
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                HStack(spacing: 4) {
                    Image(systemName: "message")
                        .foregroundColor(.secondary)
                    Text("\(post.comments)")
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                HStack(spacing: 4) {
                    Image(systemName: "eye")
                        .foregroundColor(.secondary)
                    Text("\(post.views)")
                        .foregroundColor(.secondary)
                }
            }
            .font(.subheadline)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - Create Channel View
struct CreateChannelView: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var viewModel: ChannelsViewModel
    @State private var name = ""
    @State private var description = ""
    @State private var selectedEmoji = "📢"
    @State private var isCreating = false
    
    let emojiOptions = ["📢", "💬", "🎮", "💰", "📱", "🎨", "🎵", "📚", "🏆", "🌟", "💡", "🔥", "🚀", "✨", "💼", "🎯"]
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Channel Icon") {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(emojiOptions, id: \.self) { emoji in
                                Button {
                                    selectedEmoji = emoji
                                } label: {
                                    Text(emoji)
                                        .font(.title)
                                        .padding(8)
                                        .background(
                                            selectedEmoji == emoji ?
                                            Color.menzaPurple.opacity(0.2) :
                                            Color.clear
                                        )
                                        .cornerRadius(8)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 8)
                                                .stroke(
                                                    selectedEmoji == emoji ?
                                                    Color.menzaPurple :
                                                    Color.clear,
                                                    lineWidth: 2
                                                )
                                        )
                                }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
                
                Section("Channel Info") {
                    ZStack(alignment: .leading) {
                        if name.isEmpty {
                            Text("Channel Name")
                                .foregroundColor(.gray)
                        }
                        TextField("", text: $name)
                    }
                    
                    ZStack(alignment: .topLeading) {
                        if description.isEmpty {
                            Text("Description (optional)")
                                .foregroundColor(.gray)
                                .padding(.top, 8)
                        }
                        TextField("", text: $description, axis: .vertical)
                            .lineLimit(3...6)
                    }
                }
                
                Section {
                    // Preview
                    HStack(spacing: 14) {
                        ZStack {
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [.menzaPurple, .menzaPink],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 50, height: 50)
                            
                            Text(selectedEmoji)
                                .font(.title2)
                        }
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(name.isEmpty ? "Channel Name" : "\(selectedEmoji) \(name)")
                                .font(.headline)
                                .foregroundColor(name.isEmpty ? .secondary : .primary)
                            
                            Text("0 subscribers")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                } header: {
                    Text("Preview")
                }
            }
            .navigationTitle("Create Channel")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        createChannel()
                    } label: {
                        if isCreating {
                            ProgressView()
                        } else {
                            Text("Create")
                        }
                    }
                    .disabled(name.isEmpty || isCreating)
                }
            }
        }
    }
    
    func createChannel() {
        isCreating = true
        Task {
            let fullName = "\(selectedEmoji) \(name)"
            let success = await viewModel.createChannel(name: fullName, description: description, emoji: selectedEmoji)
            isCreating = false
            if success {
                dismiss()
            }
        }
    }
}

// MARK: - View Model
@MainActor
class ChannelsViewModel: ObservableObject {
    @Published var channels: [Channel] = []
    @Published var subscribedChannels: [Channel] = []
    @Published var myChannels: [Channel] = []
    @Published var isLoading = false
    
    private let api = APIService.shared
    
    func loadChannels() async {
        isLoading = true
        
        // First load test data for immediate UI
        loadTestData()
        
        // Then try to fetch from server
        do {
            struct ChannelsResponse: Codable {
                let success: Bool
                let channels: [Channel]
            }
            
            let response: ChannelsResponse = try await api.request(
                endpoint: "/api/channels/discover",
                method: .get
            )
            
            if !response.channels.isEmpty {
                channels = response.channels
            }
        } catch {
            // Keep test data if server fails
            print("Server error, using test data: \(error)")
        }
        
        isLoading = false
    }
    
    func toggleSubscription(channelId: String) async {
        guard let index = channels.firstIndex(where: { $0.id == channelId }) else { return }
        
        let wasSubscribed = channels[index].isSubscribed
        
        // Optimistic update
        channels[index].isSubscribed.toggle()
        if wasSubscribed {
            channels[index].subscriberCount -= 1
        } else {
            channels[index].subscriberCount += 1
        }
        
        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        
        // Try to sync with server
        do {
            let endpoint = wasSubscribed ? "/api/channel/\(channelId)/unsubscribe" : "/api/channel/\(channelId)/subscribe"
            let _: GenericResponse = try await api.request(
                endpoint: endpoint,
                method: .post
            )
        } catch {
            // Revert on failure
            channels[index].isSubscribed.toggle()
            if wasSubscribed {
                channels[index].subscriberCount += 1
            } else {
                channels[index].subscriberCount -= 1
            }
            print("Subscribe toggle failed: \(error)")
        }
    }
    
    func createChannel(name: String, description: String, emoji: String) async -> Bool {
        struct CreateChannelRequest: Codable {
            let name: String
            let description: String
            let avatar: String
        }
        
        do {
            let request = CreateChannelRequest(name: name, description: description, avatar: emoji)
            let _: GenericResponse = try await api.request(
                endpoint: "/api/channel/create",
                method: .post,
                body: request
            )
            
            // Reload channels
            await loadChannels()
            return true
        } catch {
            print("Create channel failed: \(error)")
            return false
        }
    }
    
    private func loadTestData() {
        // Match backend test channels exactly from run.py
        channels = [
            Channel(
                id: "channel_tech",
                name: "Tech News Daily",
                description: "Latest tech updates",
                owner: "1zack032",
                subscriberCount: 15420,
                isVerified: true,
                isSubscribed: true,
                posts: [
                    ChannelPost(
                        id: "post1",
                        content: "🚀 Breaking: Apple announces new AI features for iOS 18! Enhanced Siri, smarter autocomplete, and more coming this fall.",
                        likes: 342,
                        comments: 56,
                        views: 2100
                    ),
                    ChannelPost(
                        id: "post2",
                        content: "💡 Tip of the day: Enable Focus Mode to boost your productivity. Here's how to set it up...",
                        likes: 128,
                        comments: 23,
                        views: 890
                    )
                ]
            ),
            Channel(
                id: "channel_crypto",
                name: "Crypto Insights",
                description: "Crypto analysis",
                owner: "1zack032",
                subscriberCount: 8750,
                isVerified: true,
                isSubscribed: false,
                posts: [
                    ChannelPost(
                        id: "post3",
                        content: "📈 Market Update: Bitcoin holds steady above $45k as institutional interest grows",
                        likes: 567,
                        comments: 89,
                        views: 4500
                    )
                ]
            ),
            Channel(
                id: "channel_menza",
                name: "Menza Updates",
                description: "Official announcements",
                owner: "1zack032",
                subscriberCount: 25000,
                isVerified: true,
                isSubscribed: true,
                posts: [
                    ChannelPost(
                        id: "post4",
                        content: "🎉 Welcome to Menza iOS! We're thrilled to launch our native app. Expect faster performance, better notifications, and a smoother experience!",
                        likes: 1250,
                        comments: 234,
                        views: 12000
                    ),
                    ChannelPost(
                        id: "post5",
                        content: "🔒 Security Update: End-to-end encryption now enabled by default for all messages. Your privacy is our priority.",
                        likes: 890,
                        comments: 145,
                        views: 8900
                    )
                ]
            )
        ]
        
        // Filter subscribed channels
        subscribedChannels = channels.filter { $0.isSubscribed }
    }
}

// MARK: - Preview
struct ChannelsView_Previews: PreviewProvider {
    static var previews: some View {
        ChannelsView()
    }
}
