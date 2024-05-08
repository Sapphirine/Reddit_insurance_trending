import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TopicsSection = () => {
    const [topics, setTopics] = useState([]);
    const [date, setDate] = useState(new Date().toISOString().slice(0, 10)); // today's date in YYYY-MM-DD format

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/topics/`, {
                    params: { date }
                });
                setTopics(response.data);
            } catch (error) {
                console.error('Error fetching topics:', error);
            }
        };

        fetchData();
    }, [date]);

    return (
        <div>
            <h1>Topics for {date}</h1>
            <button onClick={() => setDate(prevDate =>
                    new Date(new Date(prevDate).setDate(new Date(prevDate).getDate() - 1)).toISOString().slice(0, 10))}>
                    Previous Day
            </button>
            <button onClick={() => setDate(prevDate =>
                     new Date(new Date(prevDate).setDate(new Date(prevDate).getDate() + 1)).toISOString().slice(0, 10))}>
                     Next Day
            </button>
            {topics.map((topic, index) => (
                <div key={index}>
                    <h2>{topic.generated_title}</h2>
                    <p>{topic.combined_summary}</p>
                    <ul>
                        {topic.hot_posts.map((post, idx) => (
                            <li key={idx}>
                                <a href={`${post.post_url}`} target="_blank" rel="noopener noreferrer" style={{color: 'darkcyan'}}>
                                    {post.post_title}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            ))}
        </div>
    );
};

export default TopicsSection;
