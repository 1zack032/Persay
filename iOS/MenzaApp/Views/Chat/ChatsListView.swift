//
//  ChatsListView.swift
//  MenzaApp
//
//  List of all chats/conversations
//

import SwiftUI

struct ChatsListView: View {
    @StateObject private var viewModel = ChatsViewModel()
    @State private var searchText = ""
    @State private var showingNewChat = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(.systemBackground)
                    .ignoresSafeArea()
                
                if viewModel.chats.isEmpty && !viewModel.isLoading {
                    // Empty state
                    EmptyChatsView(showingNewChat: $showingNewChat)
                } else {
                    // Chats list
                    List {
                        ForEach(filteredChats) { chat in
                            NavigationLink(destination: ChatDetailView(chat: chat)) {
                                ChatRowView(chat: chat)
                            }
                            .listRowBackground(Color.clear)
                            .listRowSeparator(.hidden)
                        }
                        .onDelete(perform: deleteChat)
                    }
                    .listStyle(.plain)
                    .refreshable {
                        await viewModel.loadChats()
                    }
                }
                
                // Loading overlay
                if viewModel.isLoading {
                    ProgressView()
                        .scaleEffect(1.5)
                }
            }
            .navigationTitle("Messages")
            .searchable(text: $searchText, prompt: "Search conversations")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingNewChat = true
                    } label: {
                        Image(systemName: "square.and.pencil")
                            .foregroundColor(.menzaPurple)
                    }
                }
            }
            .sheet(isPresented: $showingNewChat) {
                NewChatView()
            }
        }
        .task {
            await viewModel.loadChats()
        }
    }
    
    var filteredChats: [Chat] {
        if searchText.isEmpty {
            return viewModel.chats
        }
        return viewModel.chats.filter { chat in
            chat.groupName?.localizedCaseInsensitiveContains(searchText) == true ||
            chat.participants.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    func deleteChat(at offsets: IndexSet) {
        // Handle deletion
    }
}

// MARK: - Chat Row
struct ChatRowView: View {
    let chat: Chat
    
    var body: some View {
        HStack(spacing: 14) {
            // Avatar
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.menzaPurple, .menzaPurpleLight],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 56, height: 56)
                
                if chat.isGroup {
                    Image(systemName: "person.3.fill")
                        .foregroundColor(Color.white)
                        .font(.title3)
                } else {
                    Text(String(displayName.prefix(1)).uppercased())
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(Color.white)
                }
            }
            
            // Content
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(displayName)
                        .font(.headline)
                        .fontWeight(.semibold)
                        .lineLimit(1)
                    
                    Spacer()
                    
                    if let time = chat.lastMessage?.timestamp {
                        Text(timeString(from: time))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                HStack {
                    Text(lastMessagePreview)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                    
                    Spacer()
                    
                    if chat.unreadCount > 0 {
                        Text("\(chat.unreadCount)")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(Color.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.menzaPurple)
                            .clipShape(Capsule())
                    }
                }
            }
        }
        .padding(.vertical, 8)
    }
    
    var displayName: String {
        if chat.isGroup {
            return chat.groupName ?? "Group"
        }
        let currentUser = UserDefaults.standard.string(forKey: "username") ?? ""
        return chat.otherParticipant(currentUser: currentUser) ?? "Chat"
    }
    
    var lastMessagePreview: String {
        guard let message = chat.lastMessage else {
            return "No messages yet"
        }
        
        let sender = message.isSentByMe ? "You: " : ""
        
        switch message.messageType {
        case .text:
            return sender + message.content
        case .image:
            return sender + "📷 Photo"
        case .video:
            return sender + "🎥 Video"
        case .audio:
            return sender + "🎤 Voice message"
        case .file:
            return sender + "📎 File"
        case .system:
            return message.content
        }
    }
    
    func timeString(from date: Date) -> String {
        let calendar = Calendar.current
        
        if calendar.isDateInToday(date) {
            let formatter = DateFormatter()
            formatter.dateFormat = "h:mm a"
            return formatter.string(from: date)
        } else if calendar.isDateInYesterday(date) {
            return "Yesterday"
        } else {
            let formatter = DateFormatter()
            formatter.dateFormat = "MMM d"
            return formatter.string(from: date)
        }
    }
}

// MARK: - Empty State
struct EmptyChatsView: View {
    @Binding var showingNewChat: Bool
    
    var body: some View {
        VStack(spacing: 24) {
            Image(systemName: "message.badge.circle.fill")
                .font(.system(size: 80))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.menzaPurple, .menzaPurpleLight],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
            
            VStack(spacing: 8) {
                Text("No Messages Yet")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Start a conversation with someone to begin messaging securely.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
            }
            
            Button {
                showingNewChat = true
            } label: {
                HStack {
                    Image(systemName: "plus")
                    Text("New Message")
                }
                .fontWeight(.semibold)
                .foregroundColor(Color.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 14)
                .background(
                    LinearGradient(
                        colors: [.menzaPurple, .menzaPurpleLight],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .cornerRadius(25)
            }
        }
    }
}

// MARK: - New Chat Hub View
struct NewChatView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    @State private var selectedOption: NewChatOption? = nil
    
    enum NewChatOption: String, CaseIterable {
        case message = "New Message"
        case group = "New Group"
        case channel = "New Channel"
        
        var icon: String {
            switch self {
            case .message: return "paperplane.fill"
            case .group: return "person.2.fill"
            case .channel: return "megaphone.fill"
            }
        }
        
        var description: String {
            switch self {
            case .message: return "Start a private conversation"
            case .group: return "Create a group chat"
            case .channel: return "Broadcast to subscribers"
            }
        }
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background gradient
                LinearGradient(
                    colors: themeManager.isDarkMode ? 
                        [Color(hex: "0D0D0D"), Color(hex: "1A1A2E")] :
                        [Color(hex: "F8F9FA"), Color(hex: "E9ECEF")],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
                
                VStack(spacing: 20) {
                    // Header icon
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.menzaPurple, .menzaPink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 70, height: 70)
                        
                        Image(systemName: "plus")
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(Color.white)
                    }
                    .padding(.top, 20)
                    
                    Text("Create New")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    // Options
                    VStack(spacing: 12) {
                        ForEach(NewChatOption.allCases, id: \.self) { option in
                            Button {
                                let generator = UIImpactFeedbackGenerator(style: .light)
                                generator.impactOccurred()
                                selectedOption = option
                            } label: {
                                HStack(spacing: 16) {
                                    // Icon with gradient
                                    ZStack {
                                        Circle()
                                            .fill(
                                                LinearGradient(
                                                    colors: [.menzaPurple.opacity(0.8), .menzaPink.opacity(0.6)],
                                                    startPoint: .topLeading,
                                                    endPoint: .bottomTrailing
                                                )
                                            )
                                            .frame(width: 48, height: 48)
                                        
                                        Image(systemName: option.icon)
                                            .font(.title3)
                                            .foregroundColor(Color.white)
                                    }
                                    
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(option.rawValue)
                                            .font(.headline)
                                            .fontWeight(.semibold)
                                            .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                                        
                                        Text(option.description)
                                            .font(.subheadline)
                                            .foregroundColor(.secondary)
                                    }
                                    
                                    Spacer()
                                    
                                    Image(systemName: "chevron.right")
                                        .font(.subheadline)
                                        .fontWeight(.semibold)
                                        .foregroundColor(.menzaPurple)
                                }
                                .padding(16)
                                .background(
                                    RoundedRectangle(cornerRadius: 16)
                                        .fill(themeManager.isDarkMode ? 
                                            Color.white.opacity(0.08) : 
                                            Color.white)
                                        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 4)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 16)
                                        .stroke(
                                            themeManager.isDarkMode ?
                                                Color.white.opacity(0.1) :
                                                Color.gray.opacity(0.1),
                                            lineWidth: 1
                                        )
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Text("Cancel")
                            .foregroundColor(.menzaPurple)
                    }
                }
            }
            .sheet(item: $selectedOption) { option in
                switch option {
                case .message:
                    NewMessageView(onComplete: { dismiss() })
                case .group:
                    NewGroupView(onComplete: { dismiss() })
                case .channel:
                    NewChannelFlowView(onComplete: { dismiss() })
                }
            }
        }
    }
}

extension NewChatView.NewChatOption: Identifiable {
    var id: String { rawValue }
}

// MARK: - Test User for Selection
struct SelectableUser: Identifiable, Equatable {
    let id: String
    let username: String
    let displayName: String?
    var isSelected: Bool = false
    var isKnown: Bool = false  // Known = previously messaged
    
    static func == (lhs: SelectableUser, rhs: SelectableUser) -> Bool {
        lhs.id == rhs.id
    }
}

// MARK: - New Message View (1-on-1 DM)
struct NewMessageView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    let onComplete: () -> Void
    
    @State private var searchText = ""
    @State private var knownUsers: [SelectableUser] = []
    @State private var otherUsers: [SelectableUser] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                (themeManager.isDarkMode ? Color(hex: "0D0D0D") : Color(hex: "F8F9FA"))
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Search bar
                    HStack(spacing: 12) {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.menzaPurple)
                        TextField("Search users", text: $searchText)
                            .textInputAutocapitalization(.never)
                    }
                    .padding(14)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                    )
                    .padding()
                    
                    // User list
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            if !filteredKnownUsers.isEmpty {
                                SectionHeader(title: "Recent")
                                ForEach(filteredKnownUsers) { user in
                                    UserRowButton(user: user) {
                                        startChat(with: user)
                                    }
                                }
                            }
                            
                            if !filteredOtherUsers.isEmpty {
                                SectionHeader(title: "All Users")
                                ForEach(filteredOtherUsers) { user in
                                    UserRowButton(user: user) {
                                        startChat(with: user)
                                    }
                                }
                            }
                            
                            if filteredKnownUsers.isEmpty && filteredOtherUsers.isEmpty && !searchText.isEmpty {
                                VStack(spacing: 12) {
                                    Image(systemName: "person.slash")
                                        .font(.largeTitle)
                                        .foregroundColor(.secondary)
                                    Text("No users found")
                                        .foregroundColor(.secondary)
                                }
                                .frame(maxWidth: .infinity)
                                .padding(.top, 40)
                            }
                        }
                        .padding(.horizontal)
                    }
                }
            }
            .navigationTitle("New Message")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
            .onAppear { loadUsers() }
        }
    }
    
    var filteredKnownUsers: [SelectableUser] {
        if searchText.isEmpty { return knownUsers }
        return knownUsers.filter {
            $0.username.localizedCaseInsensitiveContains(searchText) ||
            ($0.displayName?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }
    
    var filteredOtherUsers: [SelectableUser] {
        if searchText.isEmpty { return otherUsers }
        return otherUsers.filter {
            $0.username.localizedCaseInsensitiveContains(searchText) ||
            ($0.displayName?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }
    
    func loadUsers() {
        // Load test data - known users first
        knownUsers = [
            SelectableUser(id: "1", username: "sarah_test", displayName: "Sarah Wilson", isKnown: true),
            SelectableUser(id: "2", username: "mike_demo", displayName: "Mike Johnson", isKnown: true),
            SelectableUser(id: "3", username: "alex_dev", displayName: "Alex Chen", isKnown: true),
            SelectableUser(id: "4", username: "emma_test", displayName: "Emma Davis", isKnown: true)
        ]
        
        otherUsers = [
            SelectableUser(id: "5", username: "john_doe", displayName: "John Doe"),
            SelectableUser(id: "6", username: "jane_smith", displayName: "Jane Smith"),
            SelectableUser(id: "7", username: "crypto_trader", displayName: "Crypto Trader"),
            SelectableUser(id: "8", username: "tech_guru", displayName: "Tech Guru")
        ]
    }
    
    func startChat(with user: SelectableUser) {
        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        
        // TODO: Create/open chat with user
        print("Starting chat with: \(user.username)")
        dismiss()
        onComplete()
    }
}

// MARK: - New Group View (Multi-select)
struct NewGroupView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    let onComplete: () -> Void
    
    @State private var searchText = ""
    @State private var knownUsers: [SelectableUser] = []
    @State private var otherUsers: [SelectableUser] = []
    @State private var groupName = ""
    @State private var showingNameInput = false
    @State private var isLoading = false
    
    var selectedUsers: [SelectableUser] {
        (knownUsers + otherUsers).filter { $0.isSelected }
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                (themeManager.isDarkMode ? Color(hex: "0D0D0D") : Color(hex: "F8F9FA"))
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Selected users preview
                    if !selectedUsers.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 10) {
                                ForEach(selectedUsers) { user in
                                    SelectedUserChip(user: user) {
                                        toggleSelection(user)
                                    }
                                }
                            }
                            .padding(.horizontal)
                            .padding(.vertical, 12)
                        }
                        .background(
                            themeManager.isDarkMode ?
                                Color.menzaPurple.opacity(0.1) :
                                Color.menzaPurple.opacity(0.05)
                        )
                    }
                    
                    // Search bar
                    HStack(spacing: 12) {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.menzaPurple)
                        TextField("Search users", text: $searchText)
                            .textInputAutocapitalization(.never)
                    }
                    .padding(14)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                    )
                    .padding()
                    
                    // User list
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            if !filteredKnownUsers.isEmpty {
                                SectionHeader(title: "Recent")
                                ForEach(filteredKnownUsers) { user in
                                    UserSelectableRow(user: user) {
                                        toggleSelection(user)
                                    }
                                }
                            }
                            
                            if !filteredOtherUsers.isEmpty {
                                SectionHeader(title: "All Users")
                                ForEach(filteredOtherUsers) { user in
                                    UserSelectableRow(user: user) {
                                        toggleSelection(user)
                                    }
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                    
                    // Bottom bar with selection count
                    if !selectedUsers.isEmpty {
                        HStack {
                            Text("\(selectedUsers.count) selected")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            Spacer()
                            
                            Button {
                                showingNameInput = true
                            } label: {
                                HStack {
                                    Text("Next")
                                    Image(systemName: "arrow.right")
                                }
                                .font(.headline)
                                .foregroundColor(Color.white)
                                .padding(.horizontal, 24)
                                .padding(.vertical, 12)
                                .background(
                                    LinearGradient(
                                        colors: [.menzaPurple, .menzaPink],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .cornerRadius(25)
                            }
                            .disabled(selectedUsers.count < 2)
                        }
                        .padding()
                        .background(
                            themeManager.isDarkMode ?
                                Color(hex: "1A1A2E") :
                                Color.white
                        )
                    }
                }
            }
            .navigationTitle("New Group")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
            .sheet(isPresented: $showingNameInput) {
                GroupNameInputView(
                    groupName: $groupName,
                    memberCount: selectedUsers.count,
                    onCreate: createGroup
                )
            }
            .onAppear { loadUsers() }
        }
    }
    
    var filteredKnownUsers: [SelectableUser] {
        if searchText.isEmpty { return knownUsers }
        return knownUsers.filter {
            $0.username.localizedCaseInsensitiveContains(searchText) ||
            ($0.displayName?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }
    
    var filteredOtherUsers: [SelectableUser] {
        if searchText.isEmpty { return otherUsers }
        return otherUsers.filter {
            $0.username.localizedCaseInsensitiveContains(searchText) ||
            ($0.displayName?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }
    
    func loadUsers() {
        knownUsers = [
            SelectableUser(id: "1", username: "sarah_test", displayName: "Sarah Wilson", isKnown: true),
            SelectableUser(id: "2", username: "mike_demo", displayName: "Mike Johnson", isKnown: true),
            SelectableUser(id: "3", username: "alex_dev", displayName: "Alex Chen", isKnown: true),
            SelectableUser(id: "4", username: "emma_test", displayName: "Emma Davis", isKnown: true)
        ]
        
        otherUsers = [
            SelectableUser(id: "5", username: "john_doe", displayName: "John Doe"),
            SelectableUser(id: "6", username: "jane_smith", displayName: "Jane Smith"),
            SelectableUser(id: "7", username: "crypto_trader", displayName: "Crypto Trader"),
            SelectableUser(id: "8", username: "tech_guru", displayName: "Tech Guru")
        ]
    }
    
    func toggleSelection(_ user: SelectableUser) {
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        
        if let idx = knownUsers.firstIndex(where: { $0.id == user.id }) {
            knownUsers[idx].isSelected.toggle()
        } else if let idx = otherUsers.firstIndex(where: { $0.id == user.id }) {
            otherUsers[idx].isSelected.toggle()
        }
    }
    
    func createGroup() {
        // TODO: Create group with selected users
        print("Creating group '\(groupName)' with: \(selectedUsers.map { $0.username })")
        dismiss()
        onComplete()
    }
}

// MARK: - Group Name Input
struct GroupNameInputView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    @Binding var groupName: String
    let memberCount: Int
    let onCreate: () -> Void
    
    @State private var selectedEmoji = "👥"
    let emojiOptions = ["👥", "🚀", "💼", "🎮", "🎵", "📚", "💡", "🔥", "⚡️", "🌟", "💬", "🏆"]
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                LinearGradient(
                    colors: themeManager.isDarkMode ?
                        [Color(hex: "0D0D0D"), Color(hex: "1A1A2E")] :
                        [Color(hex: "F8F9FA"), Color(hex: "E9ECEF")],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
                
                VStack(spacing: 24) {
                    // Emoji selector with glow
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.menzaPurple, .menzaPink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 100, height: 100)
                            .shadow(color: .menzaPurple.opacity(0.5), radius: 20, x: 0, y: 10)
                        
                        Text(selectedEmoji)
                            .font(.system(size: 44))
                    }
                    .padding(.top, 30)
                    
                    // Emoji picker
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(emojiOptions, id: \.self) { emoji in
                                Button {
                                    let generator = UIImpactFeedbackGenerator(style: .light)
                                    generator.impactOccurred()
                                    selectedEmoji = emoji
                                } label: {
                                    Text(emoji)
                                        .font(.title)
                                        .padding(10)
                                        .background(
                                            RoundedRectangle(cornerRadius: 12)
                                                .fill(
                                                    selectedEmoji == emoji ?
                                                        Color.menzaPurple.opacity(0.2) :
                                                        (themeManager.isDarkMode ? Color.white.opacity(0.05) : Color.white)
                                                )
                                        )
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 12)
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
                        .padding(.horizontal)
                    }
                    
                    // Name input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Group Name")
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                        
                        TextField("Enter group name", text: $groupName)
                            .font(.body)
                            .padding(16)
                            .background(
                                RoundedRectangle(cornerRadius: 14)
                                    .fill(themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 14)
                                    .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                            )
                    }
                    .padding(.horizontal, 24)
                    
                    // Member count badge
                    HStack(spacing: 6) {
                        Image(systemName: "person.2.fill")
                            .font(.caption)
                        Text("\(memberCount) members")
                            .font(.subheadline)
                    }
                    .foregroundColor(.menzaPurple)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.menzaPurple.opacity(0.1))
                    .cornerRadius(20)
                    
                    Spacer()
                    
                    // Create button
                    Button {
                        let generator = UIImpactFeedbackGenerator(style: .medium)
                        generator.impactOccurred()
                        
                        if groupName.isEmpty {
                            groupName = "New Group"
                        }
                        groupName = "\(selectedEmoji) \(groupName)"
                        onCreate()
                        dismiss()
                    } label: {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                            Text("Create Group")
                        }
                        .font(.headline)
                        .foregroundColor(Color.white)
                        .frame(maxWidth: .infinity)
                        .padding(16)
                        .background(
                            LinearGradient(
                                colors: [.menzaPurple, .menzaPink],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(16)
                        .shadow(color: .menzaPurple.opacity(0.4), radius: 10, x: 0, y: 5)
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 24)
                }
            }
            .navigationTitle("Group Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Back") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
        }
    }
}

// MARK: - New Channel Flow View
struct NewChannelFlowView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    let onComplete: () -> Void
    
    @State private var step = 1
    @State private var channelName = ""
    @State private var channelDescription = ""
    @State private var selectedEmoji = "📢"
    @State private var moderators: [SelectableUser] = []
    @State private var knownUsers: [SelectableUser] = []
    @State private var otherUsers: [SelectableUser] = []
    @State private var searchText = ""
    
    let emojiOptions = ["📢", "💬", "🎮", "💰", "📱", "🎨", "🎵", "📚", "🏆", "🌟", "💡", "🔥", "🚀", "✨"]
    
    var body: some View {
        NavigationStack {
            if step == 1 {
                channelDetailsView
            } else {
                addModeratorsView
            }
        }
    }
    
    var channelDetailsView: some View {
        ZStack {
            // Background
            LinearGradient(
                colors: themeManager.isDarkMode ?
                    [Color(hex: "0D0D0D"), Color(hex: "1A1A2E")] :
                    [Color(hex: "F8F9FA"), Color(hex: "E9ECEF")],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 24) {
                    // Channel icon preview
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.menzaPurple, .menzaPink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 100, height: 100)
                            .shadow(color: .menzaPurple.opacity(0.5), radius: 20, x: 0, y: 10)
                        
                        Text(selectedEmoji)
                            .font(.system(size: 44))
                    }
                    .padding(.top, 20)
                    
                    // Emoji picker
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Channel Icon")
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                            .padding(.horizontal, 24)
                        
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 10) {
                                ForEach(emojiOptions, id: \.self) { emoji in
                                    Button {
                                        let generator = UIImpactFeedbackGenerator(style: .light)
                                        generator.impactOccurred()
                                        selectedEmoji = emoji
                                    } label: {
                                        Text(emoji)
                                            .font(.title)
                                            .padding(10)
                                            .background(
                                                RoundedRectangle(cornerRadius: 12)
                                                    .fill(
                                                        selectedEmoji == emoji ?
                                                            Color.menzaPurple.opacity(0.2) :
                                                            (themeManager.isDarkMode ? Color.white.opacity(0.05) : Color.white)
                                                    )
                                            )
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 12)
                                                    .stroke(
                                                        selectedEmoji == emoji ?
                                                            Color.menzaPurple : Color.clear,
                                                        lineWidth: 2
                                                    )
                                            )
                                    }
                                }
                            }
                            .padding(.horizontal, 24)
                        }
                    }
                    
                    // Channel info inputs
                    VStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Channel Name")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.secondary)
                            
                            TextField("Enter channel name", text: $channelName)
                                .font(.body)
                                .padding(16)
                                .background(
                                    RoundedRectangle(cornerRadius: 14)
                                        .fill(themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                                )
                        }
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Description (optional)")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.secondary)
                            
                            TextField("What's your channel about?", text: $channelDescription, axis: .vertical)
                                .font(.body)
                                .lineLimit(3...6)
                                .padding(16)
                                .background(
                                    RoundedRectangle(cornerRadius: 14)
                                        .fill(themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                                )
                        }
                    }
                    .padding(.horizontal, 24)
                    
                    // Preview card
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Preview")
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                        
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
                                    .frame(width: 56, height: 56)
                                
                                Text(selectedEmoji)
                                    .font(.title2)
                            }
                            
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(channelName.isEmpty ? "Channel Name" : "\(selectedEmoji) \(channelName)")
                                        .font(.headline)
                                        .fontWeight(.semibold)
                                        .foregroundColor(channelName.isEmpty ? .secondary : (themeManager.isDarkMode ? Color.white : Color.black))
                                    
                                    Image(systemName: "checkmark.seal.fill")
                                        .foregroundColor(.menzaPurple)
                                        .font(.caption)
                                }
                                
                                Text("0 subscribers")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
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
                    .padding(.horizontal, 24)
                    
                    Spacer(minLength: 100)
                }
            }
        }
        .navigationTitle("New Channel")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("Cancel") { dismiss() }
                    .foregroundColor(.menzaPurple)
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    loadUsers()
                    step = 2
                } label: {
                    HStack {
                        Text("Next")
                        Image(systemName: "arrow.right")
                    }
                    .fontWeight(.semibold)
                    .foregroundColor(channelName.isEmpty ? .secondary : .menzaPurple)
                }
                .disabled(channelName.isEmpty)
            }
        }
    }
    
    var addModeratorsView: some View {
        ZStack {
            // Background
            (themeManager.isDarkMode ? Color(hex: "0D0D0D") : Color(hex: "F8F9FA"))
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Info header
                VStack(spacing: 8) {
                    Image(systemName: "person.badge.shield.checkmark.fill")
                        .font(.title)
                        .foregroundColor(.menzaPurple)
                    
                    Text("Add Moderators")
                        .font(.headline)
                        .fontWeight(.bold)
                    
                    Text("Moderators can post content to your channel")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 20)
                .frame(maxWidth: .infinity)
                .background(
                    themeManager.isDarkMode ?
                        Color.menzaPurple.opacity(0.1) :
                        Color.menzaPurple.opacity(0.05)
                )
                
                // Selected moderators
                if !selectedModerators.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(selectedModerators) { user in
                                SelectedUserChip(user: user, role: "Moderator") {
                                    toggleModerator(user)
                                }
                            }
                        }
                        .padding(.horizontal)
                        .padding(.vertical, 12)
                    }
                }
                
                // Search bar
                HStack(spacing: 12) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.menzaPurple)
                    TextField("Search users", text: $searchText)
                        .textInputAutocapitalization(.never)
                }
                .padding(14)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                )
                .padding()
                
                // User list
                ScrollView {
                    LazyVStack(spacing: 8) {
                        if !filteredKnownUsers.isEmpty {
                            SectionHeader(title: "Recent")
                            ForEach(filteredKnownUsers) { user in
                                UserSelectableRow(user: user) {
                                    toggleModerator(user)
                                }
                            }
                        }
                        
                        if !filteredOtherUsers.isEmpty {
                            SectionHeader(title: "All Users")
                            ForEach(filteredOtherUsers) { user in
                                UserSelectableRow(user: user) {
                                    toggleModerator(user)
                                }
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Bottom bar
                HStack {
                    VStack(alignment: .leading) {
                        Text(selectedModerators.isEmpty ? "No moderators" : "\(selectedModerators.count) moderator(s)")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        Text("You can skip this step")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Button {
                        createChannel()
                    } label: {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                            Text("Create")
                        }
                        .font(.headline)
                        .foregroundColor(Color.white)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 12)
                        .background(
                            LinearGradient(
                                colors: [.menzaPurple, .menzaPink],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(25)
                    }
                }
                .padding()
                .background(
                    themeManager.isDarkMode ?
                        Color(hex: "1A1A2E") :
                        Color.white
                )
            }
        }
        .navigationTitle("Add Moderators")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button {
                    step = 1
                } label: {
                    HStack {
                        Image(systemName: "arrow.left")
                        Text("Back")
                    }
                    .foregroundColor(.menzaPurple)
                }
            }
        }
    }
    
    var selectedModerators: [SelectableUser] {
        (knownUsers + otherUsers).filter { $0.isSelected }
    }
    
    var filteredKnownUsers: [SelectableUser] {
        if searchText.isEmpty { return knownUsers }
        return knownUsers.filter {
            $0.username.localizedCaseInsensitiveContains(searchText) ||
            ($0.displayName?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }
    
    var filteredOtherUsers: [SelectableUser] {
        if searchText.isEmpty { return otherUsers }
        return otherUsers.filter {
            $0.username.localizedCaseInsensitiveContains(searchText) ||
            ($0.displayName?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }
    
    func loadUsers() {
        knownUsers = [
            SelectableUser(id: "1", username: "sarah_test", displayName: "Sarah Wilson", isKnown: true),
            SelectableUser(id: "2", username: "mike_demo", displayName: "Mike Johnson", isKnown: true),
            SelectableUser(id: "3", username: "alex_dev", displayName: "Alex Chen", isKnown: true),
            SelectableUser(id: "4", username: "emma_test", displayName: "Emma Davis", isKnown: true)
        ]
        
        otherUsers = [
            SelectableUser(id: "5", username: "john_doe", displayName: "John Doe"),
            SelectableUser(id: "6", username: "jane_smith", displayName: "Jane Smith"),
            SelectableUser(id: "7", username: "crypto_trader", displayName: "Crypto Trader"),
            SelectableUser(id: "8", username: "tech_guru", displayName: "Tech Guru")
        ]
    }
    
    func toggleModerator(_ user: SelectableUser) {
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        
        if let idx = knownUsers.firstIndex(where: { $0.id == user.id }) {
            knownUsers[idx].isSelected.toggle()
        } else if let idx = otherUsers.firstIndex(where: { $0.id == user.id }) {
            otherUsers[idx].isSelected.toggle()
        }
    }
    
    func createChannel() {
        let fullName = "\(selectedEmoji) \(channelName)"
        let mods = selectedModerators.map { $0.username }
        print("Creating channel '\(fullName)' with moderators: \(mods)")
        dismiss()
        onComplete()
    }
}

// MARK: - Reusable Components

struct SectionHeader: View {
    let title: String
    
    var body: some View {
        HStack {
            Text(title)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)
            Spacer()
        }
        .padding(.top, 16)
        .padding(.bottom, 8)
    }
}

struct UserRowButton: View {
    let user: SelectableUser
    let action: () -> Void
    @EnvironmentObject var themeManager: ThemeManager
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 14) {
                // Avatar with gradient
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
                    
                    Text(String((user.displayName ?? user.username).prefix(1)).uppercased())
                        .font(.title3)
                        .fontWeight(.bold)
                        .foregroundColor(Color.white)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(user.displayName ?? user.username)
                        .font(.body)
                        .fontWeight(.semibold)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    
                    Text("@\(user.username)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                if user.isKnown {
                    HStack(spacing: 4) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.caption2)
                        Text("Recent")
                            .font(.caption)
                    }
                    .foregroundColor(.menzaPurple)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.menzaPurple.opacity(0.15))
                    .cornerRadius(12)
                }
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(14)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill(themeManager.isDarkMode ? Color.white.opacity(0.06) : Color.white)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(
                        themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.gray.opacity(0.1),
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(.plain)
    }
}

struct UserSelectableRow: View {
    let user: SelectableUser
    var role: String? = nil
    let action: () -> Void
    @EnvironmentObject var themeManager: ThemeManager
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 14) {
                // Selection indicator
                ZStack {
                    Circle()
                        .stroke(
                            user.isSelected ? Color.menzaPurple : Color.gray.opacity(0.4),
                            lineWidth: 2
                        )
                        .frame(width: 26, height: 26)
                    
                    if user.isSelected {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.menzaPurple, .menzaPink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 18, height: 18)
                        
                        Image(systemName: "checkmark")
                            .font(.caption2)
                            .fontWeight(.bold)
                            .foregroundColor(Color.white)
                    }
                }
                
                // Avatar
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [.menzaPurple, .menzaPink],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 46, height: 46)
                    
                    Text(String((user.displayName ?? user.username).prefix(1)).uppercased())
                        .font(.headline)
                        .fontWeight(.bold)
                        .foregroundColor(Color.white)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(user.displayName ?? user.username)
                        .font(.body)
                        .fontWeight(.semibold)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    
                    Text("@\(user.username)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
            .padding(14)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill(
                        user.isSelected ?
                            Color.menzaPurple.opacity(0.1) :
                            (themeManager.isDarkMode ? Color.white.opacity(0.06) : Color.white)
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(
                        user.isSelected ?
                            Color.menzaPurple.opacity(0.5) :
                            (themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.gray.opacity(0.1)),
                        lineWidth: user.isSelected ? 2 : 1
                    )
            )
        }
        .buttonStyle(.plain)
    }
}

struct SelectedUserChip: View {
    let user: SelectableUser
    var role: String? = nil
    let onRemove: () -> Void
    @EnvironmentObject var themeManager: ThemeManager
    
    var body: some View {
        HStack(spacing: 8) {
            // Mini avatar
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.menzaPurple, .menzaPink],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 30, height: 30)
                
                Text(String((user.displayName ?? user.username).prefix(1)).uppercased())
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(Color.white)
            }
            
            VStack(alignment: .leading, spacing: 0) {
                Text(user.displayName ?? user.username)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                
                if let role = role {
                    Text(role)
                        .font(.caption2)
                        .foregroundColor(.menzaPurple)
                }
            }
            
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.menzaPurple.opacity(0.6))
                    .font(.body)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(themeManager.isDarkMode ? Color.white.opacity(0.1) : Color.white)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
        )
    }
}

// MARK: - View Model
@MainActor
class ChatsViewModel: ObservableObject {
    @Published var chats: [Chat] = []
    @Published var isLoading = false
    @Published var error: String?
    
    private let api = APIService.shared
    
    func loadChats() async {
        isLoading = true
        
        // First load test data for immediate UI
        loadTestData()
        
        // Then try to fetch from server
        do {
            struct ChatsResponse: Codable {
                let success: Bool
                let chats: [Chat]
            }
            
            let response: ChatsResponse = try await api.request(
                endpoint: "/api/chats",
                method: .get
            )
            
            if !response.chats.isEmpty {
                chats = response.chats
            }
        } catch {
            // Keep test data if server fails
            print("Server error, using test data: \(error)")
        }
        
        isLoading = false
    }
    
    private func loadTestData() {
        // Test DM conversations
        let testChats: [Chat] = [
            Chat(
                id: "dm_sarah",
                participants: ["1zack032", "sarah_test"],
                lastMessage: Message(
                    content: "Hey! How's the app coming along? 🚀",
                    sender: "sarah_test",
                    recipient: "1zack032",
                    timestamp: Date().addingTimeInterval(-300)
                ),
                unreadCount: 1,
                isGroup: false,
                groupName: "Sarah Wilson"
            ),
            Chat(
                id: "dm_mike",
                participants: ["1zack032", "mike_demo"],
                lastMessage: Message(
                    content: "Ready for our call later? Let me know!",
                    sender: "mike_demo",
                    recipient: "1zack032",
                    timestamp: Date().addingTimeInterval(-600)
                ),
                unreadCount: 0,
                isGroup: false,
                groupName: "Mike Johnson"
            ),
            Chat(
                id: "dm_alex",
                participants: ["1zack032", "alex_dev"],
                lastMessage: Message(
                    content: "Check out this new feature idea I had 💡",
                    sender: "alex_dev",
                    recipient: "1zack032",
                    timestamp: Date().addingTimeInterval(-1800)
                ),
                unreadCount: 2,
                isGroup: false,
                groupName: "Alex Chen"
            ),
            Chat(
                id: "dm_emma",
                participants: ["1zack032", "emma_test"],
                lastMessage: Message(
                    content: "The design looks amazing! ✨",
                    sender: "emma_test",
                    recipient: "1zack032",
                    timestamp: Date().addingTimeInterval(-3600)
                ),
                unreadCount: 0,
                isGroup: false,
                groupName: "Emma Davis"
            ),
            // Test Groups
            Chat(
                id: "group_startup",
                participants: ["1zack032", "sarah_test", "mike_demo"],
                lastMessage: Message(
                    content: "Let's discuss the roadmap",
                    sender: "mike_demo",
                    timestamp: Date().addingTimeInterval(-7200)
                ),
                unreadCount: 3,
                isGroup: true,
                groupName: "🚀 Startup Squad"
            ),
            Chat(
                id: "group_gaming",
                participants: ["1zack032", "alex_dev", "emma_test"],
                lastMessage: Message(
                    content: "Game night at 8pm!",
                    sender: "alex_dev",
                    timestamp: Date().addingTimeInterval(-14400)
                ),
                unreadCount: 0,
                isGroup: true,
                groupName: "🎮 Gaming Night"
            ),
            Chat(
                id: "group_work",
                participants: ["1zack032", "mike_demo", "alex_dev", "sarah_test"],
                lastMessage: Message(
                    content: "Q4 reports are ready",
                    sender: "sarah_test",
                    timestamp: Date().addingTimeInterval(-28800)
                ),
                unreadCount: 5,
                isGroup: true,
                groupName: "💼 Work Project"
            )
        ]
        
        chats = testChats
    }
}

// MARK: - Preview
struct ChatsListView_Previews: PreviewProvider {
    static var previews: some View {
        ChatsListView()
            .environmentObject(AuthService())
    }
}
