import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
import subprocess
import time

# Native page config
st.set_page_config(page_title="Simulation de Vote IA Delphi", page_icon="🗳️", layout="wide")

# --- Custom CSS---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Lora', serif !important;
}

/* Use sans-serif just for the sidebar controls and small UI elements for clarity */
[data-testid="stSidebar"] {
    font-family: 'Inter', sans-serif !important;
}

/* Monospace for metric numbers */
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.5px;
}

/* Soft paper-like cards */
[data-testid="stMetric"], .stExpander {
    background-color: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
    border-radius: 4px !important;
    padding: 1.2rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

[data-testid="stMetric"]:hover, .stExpander:hover {
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06) !important;
    transform: translateY(-1px);
}

/* Buttons rounded softly */
.stButton button {
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Headers */
h1, h2, h3 {
    color: #2D2A26 !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🗳️ Simulation de Vote IA Delphi")
st.markdown("<p style='font-size: 1.2rem; color: #5a5753; margin-bottom: 2rem;'>Analyse de la construction du consensus multi-agents via la <b>Méthode Delphi</b>.</p>", unsafe_allow_html=True)

try:
    conn = sqlite3.connect("election.db")
    
    # Try reading the data, but handle if the table is empty or doesn't exist
    try:
        df = pd.read_sql_query("SELECT * FROM votes", conn)
    except Exception:
        df = pd.DataFrame() # Empty DataFrame if table not found
    
    # --- SIDEBAR ACTIONS ---
    with st.sidebar:
        st.markdown("## ⚡ Actions du Tableau de Bord")
        
        if st.button("🔄 Actualiser les Données", use_container_width=True):
            st.rerun()
            
        if st.button("▶️ Lancer une Nouvelle Simulation", type="primary", use_container_width=True):
            with st.spinner("Les agents débattent... (cela prend une minute)"):
                # Run the simulation script
                subprocess.run(["python3", "src/simulation.py"], capture_output=True, text=True)
            st.success("Simulation Terminée !")
            time.sleep(1)
            st.rerun()
            
        if st.button("🗑️ Effacer la Base de Données", use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS votes")
            conn.commit()
            st.success("Base de données effacée.")
            time.sleep(1)
            st.rerun()
            
        st.divider()

    if not df.empty and 'run_id' in df.columns:
        
        # --- SIDEBAR CONTROLS ---
        with st.sidebar:
            st.markdown("## ⚙️ Sélection de la Simulation")
            runs = df[['run_id', 'timestamp']].drop_duplicates().sort_values('timestamp', ascending=False)
            run_options = {row['run_id']: f"{row['timestamp']} ({row['run_id'][:6]})" for _, row in runs.iterrows()}
            selected_run_id = st.selectbox("Sélectionner l'Exécution", options=list(run_options.keys()), format_func=lambda x: run_options[x])
            
            df_run = df[df['run_id'] == selected_run_id]
            rounds = sorted(df_run['round_num'].unique())
            max_round = max(rounds) if rounds else 0
            
            st.divider()
            st.markdown("### 📥 Exporter les Données")
            csv = df_run.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger l'Exécution (CSV)",
                data=csv,
                file_name=f'simulation_run_{selected_run_id[:8]}.csv',
                mime='text/csv',
                use_container_width=True
            )
            
            st.divider()
            st.info("La **Méthode Delphi** est une technique de communication structurée utilisée pour atteindre un consensus parmi des experts.")

        # --- HERO METRICS ---
        if max_round > 0:
            final_round_df = df_run[df_run['round_num'] == max_round]
            total_votes = len(final_round_df)
            winner = final_round_df['rank_1'].value_counts().idxmax()
            winner_votes = final_round_df['rank_1'].value_counts().max()
            consensus_pct = (winner_votes / total_votes) * 100
            
            final_conf = final_round_df['confidence'].mean() if 'confidence' in final_round_df.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Tours pour Terminer", max_round)
            col2.metric("Candidat Gagnant", winner, f"{consensus_pct:.1f}% de Consensus")
            col3.metric("Confiance Moyenne Finale", f"{final_conf:.1f}%" if pd.notna(final_conf) else "N/A")
            
            st.divider()
            
            # --- EVOLUTION CHARTS (CURVED) ---
            st.markdown("### 📈 Évolution Macro")
            
            all_candidates = df_run['rank_1'].dropna().unique()
            evolution_data = []
            confidence_data = []
            for r in rounds:
                df_r = df_run[df_run['round_num'] == r]
                counts = df_r['rank_1'].value_counts()
                for candidate in all_candidates:
                    count = counts.get(candidate, 0)
                    evolution_data.append({'Tour': r, 'Candidat': candidate, 'Votes': count})
                
                if 'confidence' in df_r.columns:
                    avg_conf = df_r['confidence'].dropna().mean()
                    if pd.notna(avg_conf):
                        confidence_data.append({'Tour': r, 'Confiance Moyenne': avg_conf})
            
            df_evol = pd.DataFrame(evolution_data)
            df_conf = pd.DataFrame(confidence_data)
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Pro Curves using interpolate='monotone'
                base = alt.Chart(df_evol).encode(
                    x=alt.X('Tour:Q', scale=alt.Scale(domain=[1, max_round]), axis=alt.Axis(tickMinStep=1, labelAngle=0, grid=False, labelColor='#5a5753', titleColor='#2D2A26')),
                    color=alt.Color('Candidat:N', scale=alt.Scale(range=['#C86B5E', '#627D77', '#D9A05B', '#8A9A5B']), legend=alt.Legend(orient='bottom', title=None, labelColor='#5a5753'))
                )
                line = base.mark_line(point=True, strokeWidth=4, interpolate='monotone').encode(
                    y=alt.Y('Votes:Q', scale=alt.Scale(domain=[0, 40]), axis=alt.Axis(gridOpacity=0.1, labelColor='#5a5753', titleColor='#2D2A26'))
                )
                chart = line.properties(height=350, title="Votes par Candidat").configure_view(strokeWidth=0).configure_title(color='#2D2A26', font='Lora')
                st.altair_chart(chart, use_container_width=True)
            
            with chart_col2:
                if not df_conf.empty:
                    base_conf = alt.Chart(df_conf).encode(
                        x=alt.X('Tour:Q', scale=alt.Scale(domain=[1, max_round]), axis=alt.Axis(tickMinStep=1, labelAngle=0, grid=False, labelColor='#5a5753', titleColor='#2D2A26'))
                    )
                    line_conf = base_conf.mark_line(point=True, strokeWidth=4, color='#627D77', interpolate='monotone').encode(
                        y=alt.Y('Confiance Moyenne:Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(gridOpacity=0.1, labelColor='#5a5753', titleColor='#2D2A26'))
                    )
                    # Adding a subtle area under the curve for a more "pro" dashboard look
                    area_conf = base_conf.mark_area(opacity=0.1, color='#627D77', interpolate='monotone').encode(
                        y=alt.Y('Confiance Moyenne:Q')
                    )
                    chart_conf = (area_conf + line_conf).properties(height=350, title="Confiance Moyenne des Électeurs").configure_view(strokeWidth=0).configure_title(color='#2D2A26', font='Lora')
                    st.altair_chart(chart_conf, use_container_width=True)
                else:
                    st.info("Aucune donnée de confiance disponible.")

            st.divider()
            
            # --- INTERACTIVE ROUND ANALYTICS ---
            st.header("🔍 Analyse Interactive par Tour")
            st.markdown("Faites glisser le curseur pour remonter le temps et voir l'état spécifique de la simulation à chaque tour.")
            
            selected_round = st.slider("Sélectionner la Chronologie", min_value=1, max_value=max_round, value=max_round, step=1)
            
            df_round = df_run[df_run['round_num'] == selected_round]
            
            r_col1, r_col2 = st.columns([1, 2])
            with r_col1:
                st.markdown(f"**Aperçu de la Pluralité (Tour {selected_round})**")
                plurality_counts = df_round['rank_1'].value_counts()
                st.bar_chart(plurality_counts, color="#C86B5E")
            
            with r_col2:
                st.markdown(f"**Raisonnement des Agents (Tour {selected_round})**")
                for _, row in df_round.head(10).iterrows():
                    conf_str = f" • Confiance : {row['confidence']}%" if 'confidence' in row and pd.notna(row['confidence']) else ""
                    with st.expander(f"{row['voter_id']} ({row['persona']}) → {row['rank_1']}"):
                        st.markdown(f"> *{row['reasoning']}*")
                        st.markdown(f"<small>Rang 2 : {row['rank_2']} | Rang 3 : {row['rank_3']}{conf_str}</small>", unsafe_allow_html=True)

            st.divider()
            
            # --- AGENT TRACING ---
            st.header("🕵️ Traçage des Agents")
            st.markdown("Sélectionnez un électeur individuel pour tracer comment le consensus du groupe a affecté son raisonnement privé au fil des tours.")
            
            voters = sorted(df_run['voter_id'].unique())
            selected_voter = st.selectbox("Sélectionner l'Agent à Tracer", voters)
            
            df_voter = df_run[df_run['voter_id'] == selected_voter].sort_values('round_num')
            
            if not df_voter.empty:
                persona = df_voter.iloc[0]['persona']
                st.info(f"**Persona Assigné :** {persona}")
                
                for _, row in df_voter.iterrows():
                    with st.container(border=True):
                        st.markdown(f"#### Tour {row['round_num']}")
                        conf_str = f" | Confiance : **{row['confidence']}%**" if 'confidence' in row and pd.notna(row['confidence']) else ""
                        st.markdown(f"**Vote :** 1. {row['rank_1']} | 2. {row['rank_2']} | 3. {row['rank_3']} {conf_str}")
                        st.markdown(f"> {row['reasoning']}")

    else:
        st.info("La base de données est actuellement vide. Veuillez cliquer sur **▶️ Lancer une Nouvelle Simulation** dans la barre latérale pour générer des données.")
except Exception as e:
    st.error(f"Le tableau de bord a rencontré une erreur : {e}")