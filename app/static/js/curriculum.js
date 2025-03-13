/**
 * Curriculum Browser functionality
 */
document.addEventListener('DOMContentLoaded', function() {
  // DOM elements
  const searchInput = document.getElementById('curriculum-search');
  const subjectList = document.getElementById('subject-list');
  const topicsContainer = document.getElementById('topics-container');
  const subtopicsContainer = document.getElementById('subtopics-container');
  
  let currentSubjectId = null;
  let currentTopicId = null;
  
  // Cache for user data
  const userConfidence = {};
  const userPriorities = {};
  const topicConfidence = {};
  const topicPriorities = {};
  
  // Initialize the curriculum browser
  initialize();
  
  function initialize() {
    // Load user's confidence data first, then load subjects
    loadUserConfidence()
      .then(() => {
        // Load subjects and their topics/subtopics
        loadSubjects();
        
        // Set up search functionality
        setupSearch();
      })
      .catch(error => {
        console.error('Error during initialization:', error);
      });
  }
  
  // Load user's confidence data - returns a promise for better sequencing
  function loadUserConfidence() {
    console.log('Loading user confidence data...');
    return fetch('/curriculum/api/user/confidence')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Received confidence data:', data);
        
        // Clear existing caches
        Object.keys(userConfidence).forEach(key => delete userConfidence[key]);
        Object.keys(userPriorities).forEach(key => delete userPriorities[key]);
        Object.keys(topicConfidence).forEach(key => delete topicConfidence[key]);
        Object.keys(topicPriorities).forEach(key => delete topicPriorities[key]);
        
        // Store subtopic confidence data
        if (data.confidences) {
          data.confidences.forEach(item => {
            userConfidence[item.subtopic_id] = item.level;
            userPriorities[item.subtopic_id] = item.priority;
          });
        }
        
        // Store topic confidence data
        if (data.topic_confidences) {
          data.topic_confidences.forEach(item => {
            topicConfidence[item.topic_id] = item.level;
            topicPriorities[item.topic_id] = item.priority;
          });
        }
        
        console.log('Confidence data loaded and cached');
        return data; // Return data for chaining
      })
      .catch(error => {
        console.error('Error loading user confidence data:', error);
        throw error; // Re-throw to allow handling by caller
      });
  }
  
  // Load all subjects
  function loadSubjects() {
    fetch('/curriculum/api/subjects')
      .then(response => response.json())
      .then(data => {
        if (data.subjects && data.subjects.length > 0) {
          subjectList.innerHTML = '';
          
          data.subjects.forEach(subject => {
            const subjectElement = document.createElement('li');
            subjectElement.className = 'subject-item';
            subjectElement.dataset.id = subject.id;
            
            subjectElement.innerHTML = `
              <div class="subject-header">
                <span class="subject-title">${subject.title}</span>
                <span class="subject-count">${subject.topic_count} topics</span>
              </div>
            `;
            
            subjectList.appendChild(subjectElement);
          });
          
          // Add click handler for subjects
          document.querySelectorAll('.subject-item').forEach(item => {
            item.addEventListener('click', handleSubjectClick);
          });
        } else {
          subjectList.innerHTML = '<li class="empty-state">No subjects found</li>';
        }
      })
      .catch(error => {
        console.error('Error loading subjects:', error);
        subjectList.innerHTML = '<li class="empty-state">Error loading subjects</li>';
      });
  }
  
  // Subject click handler
  function handleSubjectClick(e) {
    const subjectItem = e.currentTarget;
    const subjectId = subjectItem.dataset.id;
    
    // Deselect any previously selected subject
    document.querySelectorAll('.subject-item.selected').forEach(item => {
      item.classList.remove('selected');
    });
    
    // Select the new subject
    subjectItem.classList.add('selected');
    currentSubjectId = subjectId;
    
    // Load topics for this subject
    loadTopics(currentSubjectId);
    
    // Clear subtopics
    subtopicsContainer.innerHTML = '<p class="empty-state">Select a topic to view subtopics</p>';
  }
  
  // Load topics for a subject and also load all subtopics immediately
  function loadTopics(subjectId) {
    console.log(`Loading topics for subject ${subjectId}`);
    // Clear subtopics first
    subtopicsContainer.innerHTML = '<p class="loading-state">Loading all subtopics...</p>';
    
    fetch(`/curriculum/api/subject/${subjectId}/topics`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.topics && data.topics.length > 0) {
          topicsContainer.innerHTML = '';
          
          // Store all topics to load their subtopics
          const topicPromises = [];
          
          data.topics.forEach(topic => {
            const topicElement = document.createElement('div');
            topicElement.className = 'topic-item';
            topicElement.dataset.id = topic.id;
            
            // Get confidence level from API or cached value
            const cachedConfidence = topicConfidence[topic.id];
            const confidenceLevel = topic.confidence_level || cachedConfidence || 50;
            const isPriority = topic.priority || false;
            
            // Store the confidence value back in the cache
            topicConfidence[topic.id] = confidenceLevel;
            
            // Create the HTML structure
            topicElement.innerHTML = `
              <div class="topic-header">
                <span class="topic-title">${topic.title}</span>
                <span class="topic-count">${topic.subtopics_count} subtopics</span>
              </div>
              <p class="topic-description">${topic.description || ''}</p>
              <div class="topic-confidence">
                <div class="confidence-value">${confidenceLevel}%</div>
                <div class="confidence-bar-container">
                  <div class="confidence-bar" data-level="${confidenceLevel}"></div>
                </div>
              </div>
              <div class="topic-subtopics-container" data-topic-id="${topic.id}"></div>
            `;
            
            topicsContainer.appendChild(topicElement);
            
            // Initialize confidence bar with a slight delay to ensure styles are applied
            setTimeout(() => {
              updateConfidenceBar(topicElement, confidenceLevel);
            }, 50);
            
            // Queue this topic's subtopics to load
            topicPromises.push(loadSubtopicsForTopic(topic.id));
          });
          
          // Add click handler for topics - now just for selection, not loading
          document.querySelectorAll('.topic-item').forEach(item => {
            item.addEventListener('click', handleTopicClick);
          });
          
          // Load all subtopics for all topics
          Promise.all(topicPromises)
            .then(() => {
              console.log('All subtopics loaded successfully');
              subtopicsContainer.innerHTML = '<p class="success-state">All subtopics loaded. Click on a topic to view its subtopics.</p>';
            })
            .catch(error => {
              console.error('Error loading subtopics:', error);
              subtopicsContainer.innerHTML = '<p class="error-state">Error loading some subtopics. Please try again.</p>';
            });
        } else {
          topicsContainer.innerHTML = '<p class="empty-state">No topics found for this subject</p>';
          subtopicsContainer.innerHTML = '<p class="empty-state">No topics available</p>';
        }
      })
      .catch(error => {
        console.error('Error loading topics:', error);
        topicsContainer.innerHTML = '<p class="empty-state">Error loading topics</p>';
        subtopicsContainer.innerHTML = '<p class="empty-state">Error loading content</p>';
      });
  }
  
  // Load subtopics for a topic and store them in topic container
  function loadSubtopicsForTopic(topicId) {
    console.log(`Loading subtopics for topic ${topicId}`);
    return fetch(`/curriculum/api/topic/${topicId}/subtopics`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.subtopics && data.subtopics.length > 0) {
          // Find the container for this topic's subtopics
          const container = document.querySelector(`.topic-subtopics-container[data-topic-id="${topicId}"]`);
          if (!container) {
            console.error(`Subtopic container for topic ${topicId} not found`);
            return;
          }
          
          // Create a fragment to hold all subtopics
          const fragment = document.createDocumentFragment();
          
          data.subtopics.forEach(subtopic => {
            const subtopicElement = document.createElement('div');
            subtopicElement.className = 'subtopic-item hidden'; // Initially hidden
            subtopicElement.dataset.id = subtopic.id;
            subtopicElement.dataset.topicId = topicId;
            
            // Get user's confidence or default to 3 (middle value)
            const cachedConfidence = userConfidence[subtopic.id];
            const confidenceLevel = subtopic.confidence_level || cachedConfidence || 3;
            const isPriority = subtopic.priority || false;
            
            // Store in cache
            userConfidence[subtopic.id] = confidenceLevel;
            userPriorities[subtopic.id] = isPriority;
            
            // Create confidence indicators
            let confidenceHtml = '<div class="confidence-selector">';
            for (let i = 1; i <= 5; i++) {
              confidenceHtml += `<span class="confidence-option confidence-${i} ${i <= confidenceLevel ? 'selected' : ''}" data-level="${i}"></span>`;
            }
            confidenceHtml += '</div>';
            
            subtopicElement.innerHTML = `
              <div class="subtopic-header">
                <span class="subtopic-title">${subtopic.title}</span>
                <button class="priority-toggle ${isPriority ? 'active' : ''}" title="Toggle Priority">
                  <i class="fas fa-star"></i>
                </button>
              </div>
              <p class="subtopic-description">${subtopic.description || ''}</p>
              <p class="confidence-label">Confidence: ${confidenceLevel}/5</p>
              ${confidenceHtml}
              <p class="estimated-duration">Estimated Duration: ${subtopic.estimated_duration || 15} min</p>
            `;
            
            fragment.appendChild(subtopicElement);
          });
          
          // Add all subtopics to the container
          container.appendChild(fragment);
          
          // Add handlers for confidence selection
          container.querySelectorAll('.confidence-option').forEach(option => {
            option.addEventListener('click', handleConfidenceUpdate);
          });
          
          // Add handlers for priority toggling
          container.querySelectorAll('.priority-toggle').forEach(button => {
            button.addEventListener('click', handlePriorityToggle);
          });
          
          return data.subtopics;
        }
        return [];
      })
      .catch(error => {
        console.error(`Error loading subtopics for topic ${topicId}:`, error);
        throw error;
      });
  }
  
  // Enhanced function to update confidence bar display
  function updateConfidenceBar(topicElement, confidenceLevel) {
    const confidenceBar = topicElement.querySelector('.confidence-bar');
    const confidenceValue = topicElement.querySelector('.confidence-value');
    
    if (!confidenceBar || !confidenceValue) {
      console.warn('Could not find confidence bar elements for update', topicElement);
      return;
    }
    
    console.log(`Updating confidence bar to ${confidenceLevel}%`);
    
    // Update the value display
    confidenceValue.textContent = `${confidenceLevel}%`;
    
    // Reset width to 0 first for smooth animation when refreshing
    confidenceBar.style.width = '0%';
    
    // Update the bar's data attribute 
    confidenceBar.dataset.level = confidenceLevel;
    
    // Force a DOM reflow for smoother animation
    void confidenceBar.offsetWidth;
    
    // Now animate to the proper width
    requestAnimationFrame(() => {
      confidenceBar.style.width = `${confidenceLevel}%`;
      
      // Apply or remove the 'complete' class based on confidence level
      if (confidenceLevel === 100) {
        confidenceBar.classList.add('complete');
      } else {
        confidenceBar.classList.remove('complete');
      }
    });
  }
  
  // Topic click handler - now just shows/hides the associated subtopics
  function handleTopicClick(e) {
    const topicItem = e.currentTarget;
    const topicId = topicItem.dataset.id;
    
    // Deselect any previously selected topic
    document.querySelectorAll('.topic-item.selected').forEach(item => {
      item.classList.remove('selected');
    });
    
    // Select the new topic
    topicItem.classList.add('selected');
    currentTopicId = topicId;
    
    // Hide all subtopics first
    document.querySelectorAll('.subtopic-item').forEach(item => {
      item.classList.add('hidden');
    });
    
    // Show only the subtopics for this topic
    document.querySelectorAll(`.subtopic-item[data-topic-id="${topicId}"]`).forEach(item => {
      item.classList.remove('hidden');
    });
    
    // Update the subtopics panel title
    const topicTitle = topicItem.querySelector('.topic-title').textContent;
    subtopicsContainer.innerHTML = `
      <h3 class="selected-topic-title">${topicTitle} Subtopics</h3>
      <div id="current-subtopics-container"></div>
    `;
    
    // Move relevant subtopics to the subtopics panel for better visibility
    const currentSubtopicsContainer = document.getElementById('current-subtopics-container');
    document.querySelectorAll(`.subtopic-item[data-topic-id="${topicId}"]`).forEach(item => {
      const clone = item.cloneNode(true);
      clone.classList.remove('hidden');
      currentSubtopicsContainer.appendChild(clone);
    });
    
    // Re-attach event handlers to the cloned elements
    currentSubtopicsContainer.querySelectorAll('.confidence-option').forEach(option => {
      option.addEventListener('click', handleConfidenceUpdate);
    });
    
    currentSubtopicsContainer.querySelectorAll('.priority-toggle').forEach(button => {
      button.addEventListener('click', handlePriorityToggle);
    });
  }
  
  // Handle subtopic confidence updates
  function handleConfidenceUpdate(e) {
    try {
      e.stopPropagation(); // Prevent triggering topic clicks when updating confidence
      
      const option = e.currentTarget;
      const level = parseInt(option.dataset.level);
      const subtopicItem = option.closest('.subtopic-item');
      const subtopicId = subtopicItem.dataset.id;
      
      // Find which topic this subtopic belongs to
      const currentTopicElement = document.querySelector('.topic-item.selected');
      const topicId = currentTopicElement ? currentTopicElement.dataset.id : null;
      
      console.log('Handling confidence update:', { subtopicId, level, topicId });
    
      // Update UI for confidence selector
      subtopicItem.querySelectorAll('.confidence-option').forEach((opt, index) => {
        if (index + 1 <= level) {
          opt.classList.add('selected');
        } else {
          opt.classList.remove('selected');
        }
      });
      
      subtopicItem.querySelector('.confidence-label').textContent = `Confidence: ${level}/5`;
      
      // Update server
      console.log(`Updating subtopic ${subtopicId} confidence to level ${level}, topic=${topicId}`);
      
      fetch(`/curriculum/api/subtopic/${subtopicId}/confidence`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ level: level })
      })
      .then(response => response.json())
      .then(data => {
        console.log('Subtopic confidence updated:', data);
        
        // Check if the response includes the updated topic data
        if (data.success && data.topic) {
          console.log('Updating topic directly from response data:', data.topic);
          
          // Get the updated confidence level (now 1-100)
          const newConfidenceLevel = data.topic.confidence_level;
          
          // Find and update the topic confidence
          const topicElement = document.querySelector(`.topic-item[data-id="${topicId}"]`);
          if (topicElement) {
            // Update the topic confidence bar
            updateConfidenceBar(topicElement, newConfidenceLevel);
          } else {
            console.error('Topic element not found in DOM');
          }
        } else {
          console.error('Topic data not found in API response or no topic ID');
        }
      })
      .catch(error => {
        console.error('Error updating confidence:', error);
        showToast('Error updating confidence', 'error');
      });
      
      // Update local cache
      userConfidence[subtopicId] = level;
    } catch (error) {
      console.error('Error in handleConfidenceUpdate:', error);
    }
  }
  
  // Handle priority toggle
  function handlePriorityToggle(e) {
    try {
      e.preventDefault();
      e.stopPropagation();
      
      const button = e.currentTarget;
      const subtopicItem = button.closest('.subtopic-item');
      const subtopicId = subtopicItem.dataset.id;
      
      // Find which topic this subtopic belongs to
      const currentTopicElement = document.querySelector('.topic-item.selected');
      const topicId = currentTopicElement ? currentTopicElement.dataset.id : null;
      
      console.log('Handling priority toggle:', { subtopicId, topicId });
    
      // Toggle button state visually
      button.classList.toggle('active');
    
      // Update server
      fetch(`/curriculum/api/subtopic/${subtopicId}/priority`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      .then(response => response.json())
      .then(data => {
        console.log('Subtopic priority updated:', data);
        
        // Update local cache
        if (data.success) {
          userPriorities[subtopicId] = data.priority;
          
          // Check if the response includes the updated topic data
          if (data.topic && topicId) {
            console.log('Updating topic from priority toggle response:', data.topic);
            
            // Get the updated confidence level (now 1-100)
            const newConfidenceLevel = data.topic.confidence_level;
            
            // Find and update the topic confidence
            const topicElement = document.querySelector(`.topic-item[data-id="${topicId}"]`);
            if (topicElement) {
              // Update the topic confidence bar
              updateConfidenceBar(topicElement, newConfidenceLevel);
            }
          }
        }
      })
      .catch(error => {
        console.error('Error toggling priority:', error);
        // Revert UI change on error
        button.classList.toggle('active');
      });
    } catch (error) {
      console.error('Error in handlePriorityToggle:', error);
    }
  }
  
  // Set up search functionality
  function setupSearch() {
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
      const query = this.value.trim();
      
      if (query.length < 2) {
        // If query is too short, reset to normal view
        document.querySelectorAll('.subject-item').forEach(item => {
          item.style.display = '';
        });
        
        document.querySelectorAll('.topic-item').forEach(item => {
          item.style.display = '';
        });
        
        document.querySelectorAll('.subtopic-item').forEach(item => {
          item.style.display = '';
        });
        return;
      }
      
      fetch(`/curriculum/api/curriculum/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
          if (!data.results) return;
          
          const results = data.results;
          
          // Filter subjects
          document.querySelectorAll('.subject-item').forEach(item => {
            const subjectId = item.dataset.id;
            const matchingSubject = results.subjects.some(s => s.id.toString() === subjectId);
            const hasMatchingTopic = results.topics.some(t => t.subject_id.toString() === subjectId);
            
            if (matchingSubject || hasMatchingTopic) {
              item.style.display = '';
            } else {
              item.style.display = 'none';
            }
          });
          
          // If a subject is currently selected, filter its topics
          if (currentSubjectId) {
            document.querySelectorAll('.topic-item').forEach(item => {
              const topicId = item.dataset.id;
              const matchingTopic = results.topics.some(t => t.id.toString() === topicId);
              const hasMatchingSubtopic = results.subtopics.some(st => st.topic_id.toString() === topicId);
              
              if (matchingTopic || hasMatchingSubtopic) {
                item.style.display = '';
              } else {
                item.style.display = 'none';
              }
            });
          }
          
          // If a topic is currently selected, filter its subtopics
          if (currentTopicId) {
            document.querySelectorAll('.subtopic-item').forEach(item => {
              const subtopicId = item.dataset.id;
              const matchingSubtopic = results.subtopics.some(st => st.id.toString() === subtopicId);
              
              if (matchingSubtopic) {
                item.style.display = '';
              } else {
                item.style.display = 'none';
              }
            });
          }
        })
        .catch(error => {
          console.error('Error searching curriculum:', error);
        });
    });
  }
});
