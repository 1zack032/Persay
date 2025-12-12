//
//  ChatDetailView.swift
//  MenzaApp
//
//  Individual chat conversation view
//

import SwiftUI

struct ChatDetailView: View {
    let chat: Chat
    @StateObject private var viewModel: ChatDetailViewModel
    @State private var messageText = ""
    @FocusState private var isInputFocused: Bool
    
    // Attachment states - moved to parent level
    @State private var showingAttachmentMenu = false
    @State private var showingImagePicker = false
    @State private var showingFilePicker = false
    @State private var showingLocationPicker = false
    @State private var showingPollCreator = false
    
    init(chat: Chat) {
        self.chat = chat
        _viewModel = StateObject(wrappedValue: ChatDetailViewModel(chatId: chat.id))
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 4) {
                        ForEach(viewModel.messages) { message in
                            MessageBubbleView(message: message)
                                .id(message.id)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                }
                .onChange(of: viewModel.messages.count) { _ in
                    withAnimation {
                        if let lastMessage = viewModel.messages.last {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            // Input area
            MessageInputView(
                text: $messageText,
                isFocused: $isInputFocused,
                onSend: sendMessage,
                onAttach: {
                    showingAttachmentMenu = true
                }
            )
        }
        .navigationTitle(chatTitle)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack(spacing: 16) {
                    Button {
                        // Voice call
                    } label: {
                        Image(systemName: "phone.fill")
                            .foregroundColor(.menzaPurple)
                    }
                    
                    Button {
                        // Video call
                    } label: {
                        Image(systemName: "video.fill")
                            .foregroundColor(.menzaPurple)
                    }
                }
            }
        }
        .task {
            await viewModel.loadMessages()
        }
        // Attachment sheets at parent level
        .sheet(isPresented: $showingAttachmentMenu) {
            AttachmentMenuView(
                showingImagePicker: $showingImagePicker,
                showingFilePicker: $showingFilePicker,
                showingLocationPicker: $showingLocationPicker,
                showingPollCreator: $showingPollCreator
            )
        }
        .sheet(isPresented: $showingImagePicker) {
            ImagePickerView()
        }
        .sheet(isPresented: $showingFilePicker) {
            FilePickerView()
        }
        .sheet(isPresented: $showingLocationPicker) {
            LocationPickerView()
        }
        .sheet(isPresented: $showingPollCreator) {
            PollCreatorView()
        }
    }
    
    var chatTitle: String {
        if chat.isGroup {
            return chat.groupName ?? "Group"
        }
        let currentUser = UserDefaults.standard.string(forKey: "username") ?? ""
        return chat.otherParticipant(currentUser: currentUser) ?? "Chat"
    }
    
    func sendMessage() {
        guard !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        
        Task {
            await viewModel.sendMessage(content: messageText)
            messageText = ""
        }
    }
}

// MARK: - Message Bubble
struct MessageBubbleView: View {
    let message: Message
    
    var body: some View {
        HStack {
            if message.isSentByMe {
                Spacer(minLength: 60)
            }
            
            VStack(alignment: message.isSentByMe ? .trailing : .leading, spacing: 4) {
                // Content
                Group {
                    switch message.messageType {
                    case .text:
                        Text(message.content)
                            .foregroundColor(message.isSentByMe ? Color.white : .primary)
                    case .image:
                        AsyncImage(url: URL(string: message.mediaUrl ?? "")) { image in
                            image
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(maxWidth: 200)
                        } placeholder: {
                            ProgressView()
                        }
                        .cornerRadius(12)
                    default:
                        Text(message.content)
                            .foregroundColor(message.isSentByMe ? Color.white : .primary)
                    }
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(
                    message.isSentByMe ?
                    LinearGradient(
                        colors: [.menzaPurple, .menzaPurpleLight],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ) :
                    LinearGradient(
                        colors: [Color(.systemGray5), Color(.systemGray5)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .cornerRadius(20, corners: message.isSentByMe ? [.topLeft, .topRight, .bottomLeft] : [.topLeft, .topRight, .bottomRight])
                
                // Time
                HStack(spacing: 4) {
                    Text(timeString)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    if message.isSentByMe {
                        Image(systemName: message.isRead ? "checkmark.circle.fill" : "checkmark.circle")
                            .font(.caption2)
                            .foregroundColor(message.isRead ? .menzaPurple : .secondary)
                    }
                }
            }
            
            if !message.isSentByMe {
                Spacer(minLength: 60)
            }
        }
        .padding(.vertical, 2)
    }
    
    var timeString: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        return formatter.string(from: message.timestamp)
    }
}

// MARK: - Message Input
struct MessageInputView: View {
    @Binding var text: String
    var isFocused: FocusState<Bool>.Binding
    let onSend: () -> Void
    let onAttach: () -> Void
    
    var body: some View {
        VStack(spacing: 0) {
            Divider()
            
            HStack(spacing: 12) {
                // Attachment button
                Button {
                    let generator = UIImpactFeedbackGenerator(style: .light)
                    generator.impactOccurred()
                    onAttach()
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.title2)
                        .foregroundColor(.menzaPurple)
                }
                
                // Text field with visible placeholder
                HStack {
                    ZStack(alignment: .leading) {
                        if text.isEmpty {
                            Text("Message")
                                .foregroundColor(Color.gray)
                        }
                        TextField("", text: $text, axis: .vertical)
                            .focused(isFocused)
                            .lineLimit(5)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                }
                .background(Color(.systemGray5))
                .cornerRadius(20)
                
                // Send button
                Button(action: onSend) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title)
                        .foregroundColor(text.isEmpty ? .gray : .menzaPurple)
                }
                .disabled(text.isEmpty)
            }
            .padding(.horizontal)
            .padding(.vertical, 10)
            .background(Color(.systemBackground))
        }
    }
}

// MARK: - Attachment Menu View
struct AttachmentMenuView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    
    @Binding var showingImagePicker: Bool
    @Binding var showingFilePicker: Bool
    @Binding var showingLocationPicker: Bool
    @Binding var showingPollCreator: Bool
    
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
                
                VStack(spacing: 16) {
                    // Header
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.menzaPurple, .menzaPink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 60, height: 60)
                        
                        Image(systemName: "paperclip")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(Color.white)
                    }
                    .padding(.top, 8)
                    
                    Text("Add Attachment")
                        .font(.title3)
                        .fontWeight(.bold)
                    
                    // Options
                    VStack(spacing: 10) {
                        AttachmentMenuOption(
                            icon: "photo.fill",
                            title: "Gallery",
                            description: "Photos and videos",
                            gradientColors: [.menzaPurple, .menzaPink]
                        ) {
                            dismiss()
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                                showingImagePicker = true
                            }
                        }
                        
                        AttachmentMenuOption(
                            icon: "doc.fill",
                            title: "Files",
                            description: "iPhone or iCloud",
                            gradientColors: [.blue, .cyan]
                        ) {
                            dismiss()
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                                showingFilePicker = true
                            }
                        }
                        
                        AttachmentMenuOption(
                            icon: "location.fill",
                            title: "Location",
                            description: "Share your location",
                            gradientColors: [.green, .mint]
                        ) {
                            dismiss()
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                                showingLocationPicker = true
                            }
                        }
                        
                        AttachmentMenuOption(
                            icon: "chart.bar.fill",
                            title: "Poll",
                            description: "Create a poll",
                            gradientColors: [.orange, .pink]
                        ) {
                            dismiss()
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                                showingPollCreator = true
                            }
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
        }
    }
}

// MARK: - Attachment Menu Option
struct AttachmentMenuOption: View {
    let icon: String
    let title: String
    let description: String
    let gradientColors: [Color]
    let action: () -> Void
    @EnvironmentObject var themeManager: ThemeManager
    
    var body: some View {
        Button {
            let generator = UIImpactFeedbackGenerator(style: .light)
            generator.impactOccurred()
            action()
        } label: {
            HStack(spacing: 14) {
                // Icon with gradient
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: gradientColors,
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 46, height: 46)
                    
                    Image(systemName: icon)
                        .font(.title3)
                        .foregroundColor(Color.white)
                }
                
                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(.body)
                        .fontWeight(.semibold)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    
                    Text(description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(.menzaPurple)
            }
            .padding(14)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill((themeManager.isDarkMode ?
                        Color.white.opacity(0.08) :
                        Color.white) as Color)
                    .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 4)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
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

// MARK: - Image Picker View
struct ImagePickerView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    
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
                            .shadow(color: .menzaPurple.opacity(0.4), radius: 15, x: 0, y: 8)
                        
                        Image(systemName: "photo.fill")
                            .font(.title)
                            .foregroundColor(Color.white)
                    }
                    .padding(.top, 20)
                    
                    Text("Gallery")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("Select photos or videos")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    // Options
                    VStack(spacing: 10) {
                        AttachmentSubOption(
                            icon: "camera.fill",
                            title: "Take Photo",
                            description: "Use your camera",
                            gradientColors: [.menzaPurple, .menzaPink]
                        ) {
                            // Open camera
                        }
                        
                        AttachmentSubOption(
                            icon: "photo.on.rectangle",
                            title: "Photo Library",
                            description: "Choose from gallery",
                            gradientColors: [.blue, .purple]
                        ) {
                            // Open photo library
                        }
                        
                        AttachmentSubOption(
                            icon: "video.fill",
                            title: "Record Video",
                            description: "Capture a video",
                            gradientColors: [.red, .orange]
                        ) {
                            // Record video
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
        }
    }
}

// MARK: - File Picker View
struct FilePickerView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    
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
                                    colors: [.blue, .cyan],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 70, height: 70)
                            .shadow(color: .blue.opacity(0.4), radius: 15, x: 0, y: 8)
                        
                        Image(systemName: "doc.fill")
                            .font(.title)
                            .foregroundColor(Color.white)
                    }
                    .padding(.top, 20)
                    
                    Text("Files")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("Share documents and files")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    // Options
                    VStack(spacing: 10) {
                        AttachmentSubOption(
                            icon: "iphone",
                            title: "On My iPhone",
                            description: "Files stored locally",
                            gradientColors: [.gray, .secondary]
                        ) {
                            // Open local files
                        }
                        
                        AttachmentSubOption(
                            icon: "icloud.fill",
                            title: "iCloud Drive",
                            description: "Files in iCloud",
                            gradientColors: [.blue, .cyan]
                        ) {
                            // Open iCloud Drive
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
        }
    }
}

// MARK: - Location Picker View
struct LocationPickerView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    
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
                                    colors: [.green, .mint],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 70, height: 70)
                            .shadow(color: .green.opacity(0.4), radius: 15, x: 0, y: 8)
                        
                        Image(systemName: "location.fill")
                            .font(.title)
                            .foregroundColor(Color.white)
                    }
                    .padding(.top, 20)
                    
                    Text("Location")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("Share your location")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    // Map placeholder
                    ZStack {
                        RoundedRectangle(cornerRadius: 16)
                            .fill((themeManager.isDarkMode ? Color.white.opacity(0.06) : Color.white) as Color)
                            .frame(height: 150)
                        
                        VStack(spacing: 8) {
                            Image(systemName: "map.fill")
                                .font(.title)
                                .foregroundColor(Color.green)
                            
                            Text("Map Preview")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    // Options
                    VStack(spacing: 10) {
                        AttachmentSubOption(
                            icon: "location.fill",
                            title: "Current Location",
                            description: "Share where you are now",
                            gradientColors: [.green, .mint]
                        ) {
                            // Send current location
                        }
                        
                        AttachmentSubOption(
                            icon: "mappin.circle.fill",
                            title: "Choose on Map",
                            description: "Pick a specific location",
                            gradientColors: [.orange, .red]
                        ) {
                            // Open map picker
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
        }
    }
}

// MARK: - Poll Creator View
struct PollCreatorView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var themeManager: ThemeManager
    @State private var question = ""
    @State private var options: [String] = ["", ""]
    @State private var allowMultipleAnswers = false
    
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
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Header icon
                        ZStack {
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [.orange, .pink],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 70, height: 70)
                                .shadow(color: .orange.opacity(0.4), radius: 15, x: 0, y: 8)
                            
                            Image(systemName: "chart.bar.fill")
                                .font(.title)
                                .foregroundColor(Color.white)
                        }
                        .padding(.top, 10)
                        
                        Text("Create Poll")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        // Question input
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Question")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.secondary)
                            
                            TextField("Ask a question...", text: $question)
                                .padding(16)
                                .background(
                                    RoundedRectangle(cornerRadius: 14)
                                        .fill((themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white) as Color)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(Color.menzaPurple.opacity(0.3), lineWidth: 1)
                                )
                        }
                        .padding(.horizontal, 20)
                        
                        // Options
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Options")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.secondary)
                                .padding(.horizontal, 20)
                            
                            ForEach(0..<options.count, id: \.self) { index in
                                HStack {
                                    HStack {
                                        Circle()
                                            .fill(Color.menzaPurple.opacity(0.2))
                                            .frame(width: 24, height: 24)
                                            .overlay(
                                                Text("\(index + 1)")
                                                    .font(.caption)
                                                    .fontWeight(.bold)
                                                    .foregroundColor(.menzaPurple)
                                            )
                                        
                                        TextField("Option \(index + 1)", text: $options[index])
                                    }
                                    .padding(14)
                                    .background(
                                        RoundedRectangle(cornerRadius: 14)
                                            .fill((themeManager.isDarkMode ? Color.white.opacity(0.08) : Color.white) as Color)
                                    )
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 14)
                                            .stroke(Color.gray.opacity(0.15), lineWidth: 1)
                                    )
                                    
                                    if options.count > 2 {
                                        Button {
                                            withAnimation {
                                                var mutableOptions = options
                                                mutableOptions.remove(at: index)
                                                options = mutableOptions
                                            }
                                        } label: {
                                            Image(systemName: "minus.circle.fill")
                                                .font(.title2)
                                                .foregroundColor(Color.red.opacity(0.8))
                                        }
                                    }
                                }
                                .padding(.horizontal, 20)
                            }
                            
                            if options.count < 6 {
                                Button {
                                    withAnimation {
                                        options.append("")
                                    }
                                } label: {
                                    HStack {
                                        Image(systemName: "plus.circle.fill")
                                            .font(.title3)
                                        Text("Add Option")
                                            .fontWeight(.medium)
                                    }
                                    .foregroundColor(.menzaPurple)
                                }
                                .padding(.horizontal, 20)
                            }
                        }
                        
                        // Settings
                        Toggle(isOn: $allowMultipleAnswers) {
                            HStack {
                                Image(systemName: "checklist")
                                    .foregroundColor(.menzaPurple)
                                Text("Allow multiple answers")
                            }
                        }
                        .tint(.menzaPurple)
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 14)
                                .fill((themeManager.isDarkMode ? Color.white.opacity(0.06) : Color.white) as Color)
                        )
                        .padding(.horizontal, 20)
                        
                        // Create button
                        Button {
                            // Create poll
                            dismiss()
                        } label: {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                Text("Create Poll")
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
                            .cornerRadius(14)
                            .shadow(color: .menzaPurple.opacity(0.4), radius: 10, x: 0, y: 5)
                        }
                        .disabled(question.isEmpty || options.filter { !$0.isEmpty }.count < 2)
                        .opacity(question.isEmpty || options.filter { !$0.isEmpty }.count < 2 ? 0.6 : 1)
                        .padding(.horizontal, 20)
                        .padding(.top, 10)
                        
                        Spacer(minLength: 40)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.menzaPurple)
                }
            }
        }
    }
}

// MARK: - Attachment Sub Option
struct AttachmentSubOption: View {
    let icon: String
    let title: String
    let description: String
    let gradientColors: [Color]
    let action: () -> Void
    @EnvironmentObject var themeManager: ThemeManager
    
    var body: some View {
        Button {
            let generator = UIImpactFeedbackGenerator(style: .light)
            generator.impactOccurred()
            action()
        } label: {
            HStack(spacing: 14) {
                // Icon with gradient
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: gradientColors,
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 44, height: 44)
                    
                    Image(systemName: icon)
                        .font(.title3)
                        .foregroundColor(Color.white)
                }
                
                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(.body)
                        .fontWeight(.semibold)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    
                    Text(description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
            }
            .padding(14)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill((themeManager.isDarkMode ?
                        Color.white.opacity(0.08) :
                        Color.white) as Color)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
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

// MARK: - Corner Radius Extension
extension View {
    func cornerRadius(_ radius: CGFloat, corners: UIRectCorner) -> some View {
        clipShape(RoundedCorner(radius: radius, corners: corners))
    }
}

struct RoundedCorner: Shape {
    var radius: CGFloat = .infinity
    var corners: UIRectCorner = .allCorners
    
    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(
            roundedRect: rect,
            byRoundingCorners: corners,
            cornerRadii: CGSize(width: radius, height: radius)
        )
        return Path(path.cgPath)
    }
}

// MARK: - View Model
@MainActor
class ChatDetailViewModel: ObservableObject {
    let chatId: String
    @Published var messages: [Message] = []
    @Published var isLoading = false
    
    private let api = APIService.shared
    private let currentUser = UserDefaults.standard.string(forKey: "username") ?? "1zack032"
    
    init(chatId: String) {
        self.chatId = chatId
    }
    
    func loadMessages() async {
        isLoading = true
        
        // First load test messages for immediate UI
        loadTestMessages()
        
        // Then try to fetch from server
        do {
            struct MessagesResponse: Codable {
                let success: Bool
                let messages: [Message]
            }
            
            let response: MessagesResponse = try await api.request(
                endpoint: "/api/messages/\(chatId)",
                method: .get
            )
            
            if !response.messages.isEmpty {
                messages = response.messages.sorted { $0.timestamp < $1.timestamp }
            }
        } catch {
            // Keep test messages if server fails
            print("Server error, using test data: \(error)")
        }
        
        isLoading = false
    }
    
    private func loadTestMessages() {
        let otherUser = getOtherUser()
        
        // Sample conversation based on chat
        let testConversations: [String: [Message]] = [
            "dm_sarah": [
                Message(content: "Hey! 👋", sender: "sarah_test", recipient: currentUser, timestamp: Date().addingTimeInterval(-3600)),
                Message(content: "Hi Sarah! How are you?", sender: currentUser, recipient: "sarah_test", timestamp: Date().addingTimeInterval(-3500)),
                Message(content: "I'm great! Working on some new designs", sender: "sarah_test", recipient: currentUser, timestamp: Date().addingTimeInterval(-3400)),
                Message(content: "That sounds awesome! Can't wait to see them", sender: currentUser, recipient: "sarah_test", timestamp: Date().addingTimeInterval(-3300)),
                Message(content: "Hey! How's the app coming along? 🚀", sender: "sarah_test", recipient: currentUser, timestamp: Date().addingTimeInterval(-300))
            ],
            "dm_mike": [
                Message(content: "Hey Mike, meeting at 3?", sender: currentUser, recipient: "mike_demo", timestamp: Date().addingTimeInterval(-7200)),
                Message(content: "Yes! Let's do a video call", sender: "mike_demo", recipient: currentUser, timestamp: Date().addingTimeInterval(-7000)),
                Message(content: "Perfect, I'll set it up", sender: currentUser, recipient: "mike_demo", timestamp: Date().addingTimeInterval(-6800)),
                Message(content: "Ready for our call later? Let me know!", sender: "mike_demo", recipient: currentUser, timestamp: Date().addingTimeInterval(-600))
            ],
            "dm_alex": [
                Message(content: "Yo Alex! 🎮", sender: currentUser, recipient: "alex_dev", timestamp: Date().addingTimeInterval(-14400)),
                Message(content: "What's up! Ready for game night?", sender: "alex_dev", recipient: currentUser, timestamp: Date().addingTimeInterval(-14200)),
                Message(content: "Always! What are we playing?", sender: currentUser, recipient: "alex_dev", timestamp: Date().addingTimeInterval(-14000)),
                Message(content: "Check out this new feature idea I had 💡", sender: "alex_dev", recipient: currentUser, timestamp: Date().addingTimeInterval(-1800))
            ],
            "dm_emma": [
                Message(content: "Hey Emma! Love your latest design work", sender: currentUser, recipient: "emma_test", timestamp: Date().addingTimeInterval(-28800)),
                Message(content: "Thank you so much! 🥰", sender: "emma_test", recipient: currentUser, timestamp: Date().addingTimeInterval(-28600)),
                Message(content: "Would love to collaborate sometime", sender: currentUser, recipient: "emma_test", timestamp: Date().addingTimeInterval(-28400)),
                Message(content: "The design looks amazing! Great work! ✨", sender: "emma_test", recipient: currentUser, timestamp: Date().addingTimeInterval(-3600))
            ],
            "group_startup": [
                Message(content: "Welcome to Startup Squad! 🚀", sender: "mike_demo", timestamp: Date().addingTimeInterval(-86400)),
                Message(content: "Excited to be here!", sender: "sarah_test", timestamp: Date().addingTimeInterval(-86000)),
                Message(content: "Let's build something amazing", sender: currentUser, timestamp: Date().addingTimeInterval(-85000)),
                Message(content: "First item: product roadmap", sender: "mike_demo", timestamp: Date().addingTimeInterval(-80000)),
                Message(content: "Let's discuss the roadmap", sender: "mike_demo", timestamp: Date().addingTimeInterval(-7200))
            ],
            "group_gaming": [
                Message(content: "Who's online tonight? 🎮", sender: "alex_dev", timestamp: Date().addingTimeInterval(-50000)),
                Message(content: "I'm in!", sender: currentUser, timestamp: Date().addingTimeInterval(-49000)),
                Message(content: "Count me in too! 🙋‍♀️", sender: "emma_test", timestamp: Date().addingTimeInterval(-48000)),
                Message(content: "Game night at 8pm!", sender: "alex_dev", timestamp: Date().addingTimeInterval(-14400))
            ],
            "group_work": [
                Message(content: "Morning team! ☕", sender: "sarah_test", timestamp: Date().addingTimeInterval(-172800)),
                Message(content: "Good morning!", sender: currentUser, timestamp: Date().addingTimeInterval(-172000)),
                Message(content: "Let's crush it today 💪", sender: "alex_dev", timestamp: Date().addingTimeInterval(-171000)),
                Message(content: "Meeting at 2pm", sender: "mike_demo", timestamp: Date().addingTimeInterval(-100000)),
                Message(content: "Q4 reports are ready", sender: "sarah_test", timestamp: Date().addingTimeInterval(-28800))
            ]
        ]
        
        // Find matching conversation or use generic messages
        if let convo = testConversations[chatId] {
            messages = convo
        } else {
            // Generic fallback
            messages = [
                Message(content: "Hey there! 👋", sender: otherUser, recipient: currentUser, timestamp: Date().addingTimeInterval(-3600)),
                Message(content: "Hi! How are you?", sender: currentUser, recipient: otherUser, timestamp: Date().addingTimeInterval(-3500)),
                Message(content: "I'm doing great, thanks for asking!", sender: otherUser, recipient: currentUser, timestamp: Date().addingTimeInterval(-3400))
            ]
        }
    }
    
    private func getOtherUser() -> String {
        // Extract other user from chat ID if it's a DM
        if chatId.hasPrefix("dm_") {
            let parts = chatId.replacingOccurrences(of: "dm_", with: "").components(separatedBy: "_")
            return parts.first(where: { $0 != currentUser }) ?? parts.last ?? "user"
        }
        return "other_user"
    }
    
    func sendMessage(content: String) async {
        // Add message locally immediately
        let newMessage = Message(
            content: content,
            sender: currentUser,
            recipient: getOtherUser(),
            timestamp: Date()
        )
        messages.append(newMessage)
        
        // Then try to send to server
        struct SendMessageRequest: Codable {
            let content: String
            let chat_id: String
        }
        
        do {
            let request = SendMessageRequest(content: content, chat_id: chatId)
            let _: GenericResponse = try await api.request(
                endpoint: "/api/messages/send",
                method: .post,
                body: request
            )
        } catch {
            print("Failed to send message to server: \(error)")
            // Message is still shown locally
        }
    }
}

// MARK: - Preview
struct ChatDetailView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            ChatDetailView(chat: Chat(
                id: "1",
                participants: ["user1", "user2"],
                lastMessage: nil,
                unreadCount: 0,
                isGroup: false,
                groupName: nil,
                groupAvatar: nil,
                createdAt: Date()
            ))
        }
    }
}
