
  Parameter Count Breakdown

  The 7.4M is the total non-zero parameters after training. The expansion factors scale up
   the model architecture, but sparsity keeps the actual stored parameters constant:

  | Expansion | d_model | n_head | d_mlp  | d_head | Actual Params | Config Name
                   |
  |-----------|---------|--------|--------|--------|---------------|----------------------
  -----------------|
  | 1x        | 256     | 16     | 1,024  | 16     | 7.4M          |
  csp_sweep1_1x_7.4Mnonzero_afrac1.000  |
  | 2x        | 512     | 32     | 2,048  | 16     | 7.4M          |
  csp_sweep1_2x_7.4Mnonzero_afrac1.000  |
  | 4x        | 1,024   | 64     | 4,096  | 16     | 7.4M          |
  csp_sweep1_4x_7.4Mnonzero_afrac1.000  |
  | 16x       | 4,096   | 64     | 16,384 | 64     | 7.4M          |
  csp_sweep1_16x_7.4Mnonzero_afrac0.125 |

  How It Works

  1. Expansion factor scales the architecture: The expansion_factor directly multiplies
  d_model and d_mlp, making wider hidden layers
    - 1x: d_model = 256, d_mlp = 1,024
    - 2x: d_model = 512, d_mlp = 2,048 (doubled)
    - 4x: d_model = 1,024, d_mlp = 4,096 (quadrupled)
    - 16x: d_model = 4,096, d_mlp = 16,384 (16x larger!)
  2. But activation sparsity (afrac) keeps parameter count constant: The 16x model can be
  much wider, but by using aggressive sparsity (afrac=0.125 = keep only 12.5% of
  activations), the actual non-zero parameters stay at ~7.4M
  3. Why this matters for your paper:
    - You can compare models with same parameter efficiency (7.4M non-zero) but different 
  capacities
    - Larger models with sparsity can have more complex circuits without exceeding the
  parameter budget
    - This tests: "Do bigger sparse models learn simpler circuits?" (Figure 3)

  So 7.4M is not the total possible parameters—it's the stored/non-zero parameters after 
  pruning and sparsity. All these models have ~7.4M active weights but very different
  architectures and capacities.

> what exactly is the streamlit app in circuit_sparsity/viz.py showing? what kind of data 
does it show, and where is it stored/pulled from? 

  Overview

  The Streamlit visualization app is an interactive circuit visualization tool for
  exploring how neural networks learn interpretable circuits (sub-networks of neurons that
   solve specific tasks). It shows:

  1. Circuit structure - which neurons/attention heads are important
  2. Connection strengths - how strongly neurons influence each other
  3. Token-level activations - which parts of the input code activate specific neurons
  4. Loss curves - how performance changes as circuits are pruned

  Key Data & Where It's Stored

  Data Structure (line 1326-1432)

  The app loads data from this path:
  {MODEL_BASE_DIR}/viz/{model_name}/{dataset_name}/{sweep_name}/{k}/viz_data.pt

  Example: viz/csp_yolo1/single_double_quote/acdc_pruned/128/viz_data.pt

  Where:
  - model_name: csp_yolo1, csp_yolo2 (model being analyzed)
  - dataset_name: single_double_quote, bracket_counting_beeg (task)
  - sweep_name: acdc_pruned, etc. (pruning method)
  - k: 128, 256, etc. (circuit size - how many nodes to keep)

  What's Inside viz_data.pt (loaded at line 224-242)

  The loaded viz_data dictionary contains:

  {
    "circuit_data":     # Pruned nodes/edges retained 
    {
      "0.mlp.post_act": [...],  # nodes in layer 0 MLP post-activation
      "0.attn.v": [...],         # nodes in layer 0 attention value heads
      ...
    },

    "samples": {
      # Token examples that activate specific neurons
      "2.mlp.post_act": {
        407: {  # neuron index
          0.001: [[doc_tokens], [activations], [position]],  # bottom 0.1%
          0.01: [...],                                        # bottom 1%
          ...
        }
      }
    },

    "importances": {
      "ch_interv_losses": {...},      # importance scores per layer
      "pair_data": [...],             # edge importance matrices
      "loss": float,                  # baseline loss
      "interv_loss": float,           # loss after pruning circuit
      "beeg_model_config": GPTConfig, # model architecture config
      "task_samples": [docs, activations]  # all task examples
    },

    "all_loss": [[step, loss], ...],  # loss curve during pruning
    "num_total_nodes": int,           # total neurons in circuit
  }

  What the App Visualizes (Main Sections)

  1. Circuit Graph (lines 648-850)

  Interactive visualization showing:
  - Nodes (circles) = neurons/channels, colored by importance
  - Edges (arrows) = connections between layers
  - Layers: activations → processing → residual output

  You can:
  - Select layer (MLP or attention)
  - Adjust edge strength threshold (slider, line 784)
  - Click nodes to inspect them

  2. Token Activations Panel (lines 851-1199)

  Right side shows details for selected neuron:
  - Pretraining samples: Shows code snippets with highlighted tokens that activate this
  neuron (lines 930-987)
    - "Bottom" = examples where neuron fires weakly
    - "Top" = examples where neuron fires strongly
    - Color intensity = activation strength
  - Task distribution: Shows task examples with neuron activations (lines 988-1199)
    - Class 1 vs Class 2 (e.g., code with single quotes vs double quotes)
    - Heatmap shows which tokens the neuron responds to
    - Supports attention visualization (attention pattern between query/key)

  3. Faithfulness Curve (lines 1231-1281)

  Shows how loss changes as circuit size increases:
  - X-axis = circuit size (log scale)
  - Y-axis = loss (log scale)
  - Blue line = empirical loss at each k

  4. Pruning Loss Curve (lines 1284-1323)

  Shows optimization progress during circuit discovery

  5. Embedding Analysis (lines 1477-1585)

  Tab 2 visualizes:
  - Token embeddings (top/bottom weighted tokens per channel)
  - Position embeddings (wpe heatmap)

  Data Flow Summary

  Model Training
      ↓
  Circuit Discovery (e.g., ACDC pruning)
      ↓
  Generate viz_data.pt containing:
    - Which neurons matter (circuit_data)
    - Examples that activate them (samples)
    - Importance scores (importances)
      ↓
  Streamlit App
      ↓
  User selects model/task/pruning method/k
      ↓
  Loads viz_data.pt
      ↓
  Displays circuit graph + token activations

  Key Functions

  - jacob_viz() (line 648) - Main visualization function
  - build_figure() (line 292) - Renders circuit graph
  - load_data() (line 224) - Loads viz_data.pt from Azure blob storage
  - display_code_heatmap() (line 74) - Renders tokens with activation colors

  The app essentially lets you explore which neurons solve a task, and what patterns they 
  detect in the training data.