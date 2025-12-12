//
//  Message.swift
//  MenzaApp
//
//  Message and Chat models
//

import Foundation

struct Message: Codable, Identifiable, Equatable {
    let id: String
    let content: String
    let sender: String
    let recipient: String?
    let groupId: String?
    let timestamp: Date
    var isRead: Bool
    var isDelivered: Bool
    let messageType: MessageType
    var mediaUrl: String?
    var replyTo: String?
    
    enum MessageType: String, Codable {
        case text
        case image
        case video
        case audio
        case file
        case system
    }
    
    enum CodingKeys: String, CodingKey {
        case id
        case content
        case sender
        case recipient
        case groupId = "group_id"
        case timestamp
        case isRead = "is_read"
        case isDelivered = "is_delivered"
        case messageType = "message_type"
        case mediaUrl = "media_url"
        case replyTo = "reply_to"
    }
    
    var isSentByMe: Bool {
        sender == UserDefaults.standard.string(forKey: "username")
    }
    
    static func == (lhs: Message, rhs: Message) -> Bool {
        lhs.id == rhs.id
    }
    
    // Explicit initializer for creating messages locally
    init(
        id: String = UUID().uuidString,
        content: String,
        sender: String,
        recipient: String? = nil,
        groupId: String? = nil,
        timestamp: Date = Date(),
        isRead: Bool = false,
        isDelivered: Bool = false,
        messageType: MessageType = .text,
        mediaUrl: String? = nil,
        replyTo: String? = nil
    ) {
        self.id = id
        self.content = content
        self.sender = sender
        self.recipient = recipient
        self.groupId = groupId
        self.timestamp = timestamp
        self.isRead = isRead
        self.isDelivered = isDelivered
        self.messageType = messageType
        self.mediaUrl = mediaUrl
        self.replyTo = replyTo
    }
}

// MARK: - Chat/Conversation
struct Chat: Codable, Identifiable {
    let id: String
    let participants: [String]
    var lastMessage: Message?
    var unreadCount: Int
    let isGroup: Bool
    var groupName: String?
    var groupAvatar: String?
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case participants
        case lastMessage = "last_message"
        case unreadCount = "unread_count"
        case isGroup = "is_group"
        case groupName = "group_name"
        case groupAvatar = "group_avatar"
        case createdAt = "created_at"
    }
    
    // Get the other participant's username (for 1-on-1 chats)
    func otherParticipant(currentUser: String) -> String? {
        participants.first { $0 != currentUser }
    }
    
    // Explicit initializer for creating chats locally/previews
    init(
        id: String = UUID().uuidString,
        participants: [String],
        lastMessage: Message? = nil,
        unreadCount: Int = 0,
        isGroup: Bool = false,
        groupName: String? = nil,
        groupAvatar: String? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.participants = participants
        self.lastMessage = lastMessage
        self.unreadCount = unreadCount
        self.isGroup = isGroup
        self.groupName = groupName
        self.groupAvatar = groupAvatar
        self.createdAt = createdAt
    }
}

// MARK: - ChatGroup (renamed from Group to avoid SwiftUI conflict)
struct ChatGroup: Codable, Identifiable {
    let id: String
    var name: String
    var description: String?
    var avatar: String?
    var members: [String]
    var admins: [String]
    let creator: String
    let createdAt: Date
    var inviteLink: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case avatar
        case members
        case admins
        case creator
        case createdAt = "created_at"
        case inviteLink = "invite_link"
    }
}
